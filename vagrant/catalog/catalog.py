from flask import Flask, request, session, redirect, flash, url_for, render_template, abort
from models.index import City, Base, Restaurant, User, Complaint, Recommendation
from sqlalchemy.orm import sessionmaker
from sqlalchemy import asc, create_engine
from flask import session as login_session
import random
import string
from oauth2client.client import flow_from_clientsecrets
from oauth2client.client import FlowExchangeError
import httplib2
import json
from flask import make_response
import requests

app = Flask(__name__)
app.secret_key = "SECRET_KEY"
engine = create_engine("postgresql:///catalogdb")
Base.metadata.bind = engine
DBSession = sessionmaker(bind=engine)
session = DBSession()

CLIENT_ID = json.loads(
    open('client_secrets.json', 'r').read())['web']['client_id']
APPLICATION_NAME = "Restaurant Menu Application"


@app.route("/")
def showSignIn():
    return render_template("signin.html")


@app.route("/signin/user")
def showSignInUser():
    state = ''.join(random.choice(string.ascii_uppercase + string.digits)
                    for x in xrange(32))
    login_session['state'] = state
    login_session['admin'] = False
    return render_template("login.html", STATE=state)


@app.route("/signin/admin")
def showSignInAdmin():
    state = ''.join(random.choice(string.ascii_uppercase + string.digits)
                    for x in xrange(32))
    login_session['state'] = state
    login_session['admin'] = True
    return render_template("login.html", STATE=state)


def getUserData(credentials):
    userinfo_url = "https://www.googleapis.com/oauth2/v1/userinfo"
    params = {'access_token': credentials.access_token, 'alt': 'json'}
    answer = requests.get(userinfo_url, params=params)
    return answer.json()


def saveUserToDB(data):
    login_session['username'] = data['name'] if 'name' in data else ''
    login_session['email'] = data['email']
    if session.query(User).filter_by(email=data['email']).first() is None:
        user = User(
            name=login_session['username'],
            email=data['email'],
            is_admin=login_session['admin'])
        session.add(user)
        flash('New user `%s` was created' % user.name)


@app.route('/gconnect/', methods=['POST'])
def gconnect():
    if request.args.get('state') != login_session['state']:
        response = make_response(json.dumps('Invalid state parameter.'), 401)
        response.headers['Content-Type'] = 'application/json'
        return response
    code = request.data
    try:
        oauth_flow = flow_from_clientsecrets('client_secrets.json', scope='')
        oauth_flow.redirect_uri = 'postmessage'
        credentials = oauth_flow.step2_exchange(code)
    except FlowExchangeError:
        response = make_response(
            json.dumps('Failed to upgrade the authorization code.'), 401)
        response.headers['Content-Type'] = 'application/json'
        return response
    access_token = credentials.access_token
    url = ('https://www.googleapis.com/oauth2/v1/tokeninfo?access_token=%s'
           % access_token)
    h = httplib2.Http()
    result = json.loads(h.request(url, 'GET')[1])
    if result.get('error') is not None:
        response = make_response(json.dumps(result.get('error')), 500)
        response.headers['Content-Type'] = 'application/json'
        return response
    gplus_id = credentials.id_token['sub']
    if result['user_id'] != gplus_id:
        response = make_response(
            json.dumps("Token's user ID doesn't match given user ID."), 401)
        response.headers['Content-Type'] = 'application/json'
        return response
    if result['issued_to'] != CLIENT_ID:
        response = make_response(
            json.dumps("Token's client ID does not match app's."), 401)
        print "Token's client ID does not match app's."
        response.headers['Content-Type'] = 'application/json'
        return response
    stored_access_token = login_session.get('access_token')
    stored_gplus_id = login_session.get('gplus_id')
    data = getUserData(credentials)
    saveUserToDB(data)
    if stored_access_token is not None and gplus_id == stored_gplus_id:
        response = make_response(json.dumps('Current user is already connected.'),
                                 200)
        response.headers['Content-Type'] = 'application/json'
        return response
    login_session['access_token'] = credentials.access_token
    login_session['gplus_id'] = gplus_id
    return 'True'


@app.route("/city/new/", methods=["GET", "POST"])
def newCity():
    if request.method == "POST":
        city = City(name=request.form["city"], country=request.form["country"])
        session.add(city)
        flash('New city `%s` was created' % city.name)
        session.commit()
        return redirect(url_for('showCities'))
    else:
        return render_template('newCity.html')


@app.route('/city/all/')
def showCities():
    cities = session.query(City).order_by(asc(City.name))
    return render_template('cities.html', cities=cities)


@app.route("/city/<int:city_id>/restaurant/new/", methods=["GET", "POST"])
def newRestaurant(city_id):
    if request.method == "POST":
        restaurant = Restaurant(name=request.form["name"], description=request.form["description"],
                                city_id=city_id)
        session.add(restaurant)
        flash(
            'New restaurant `%s` in city with id: %d was created' %
            (restaurant.name, city_id))
        session.commit()
        return redirect(url_for('showRestaurants', city_id=city_id))
    else:
        city = session.query(City).get(city_id)
        return render_template('newRestaurant.html', city=city)


@app.route('/city/<int:city_id>/restaurant/all/')
def showRestaurants(city_id):
    city = session.query(City).get(city_id)
    if city_id == 0:
        restaurants = session.query(Restaurant).all()
    else:
        restaurants = session.query(Restaurant).filter_by(
            city_id=city_id).order_by(asc(Restaurant.name))
    return render_template(
        'restaurants.html', restaurants=restaurants, city=city)


@app.route("/user/new/", methods=["GET", "POST"])
def newUser():
    if request.method == "POST":
        is_admin = True if request.form["is_admin"] == "true" else False
        user = User(
            name=request.form["name"],
            email=request.form["email"],
            is_admin=is_admin)
        session.add(user)
        flash('New user `%s` was created' % user.name)
        session.commit()
        return redirect(url_for('showUsers'))
    else:
        return render_template('newUser.html')


@app.route('/user/all/')
def showUsers():
    users = session.query(User)
    return render_template('users.html', users=users)


@app.route('/user/<int:user_id>/')
def showUser(user_id):
    user = session.query(User).get(user_id)
    return render_template('user.html', user=user)


@app.route("/restaurant/<int:restaurant_id>/comment/new/",
           methods=["GET", "POST"])
def newComment(restaurant_id):
    if request.method == "POST":
        if request.form["type"] == "complaint":
            complaint = Complaint(name=request.form["name"],
                                  description=request.form["description"],
                                  rate=int(request.form["rate"]),
                                  restaurant_id=restaurant_id,
                                  posted_by=2  # TODO: change when auth is added
                                  )
            session.add(complaint)
            flash(
                'New complaint `%s` in restaurant with id: %d was created' %
                (complaint.name, restaurant_id))
        elif request.form["type"] == "recommendation":
            recommendation = Recommendation(name=request.form["name"],
                                            description=request.form["description"],
                                            restaurant_id=restaurant_id,
                                            posted_by=2  # TODO: change when auth is added
                                            )
            session.add(recommendation)
            flash(
                'New recommendation `%s` in restaurant with id: %d was created' %
                (recommendation.name, restaurant_id))
        else:
            return abort(400)
        session.commit()
        return redirect(url_for('showComments', restaurant_id=restaurant_id))
    else:
        restaurant = session.query(Restaurant).get(restaurant_id)
        return render_template('newComment.html', restaurant=restaurant)


@app.route('/restaurant/<int:restaurant_id>/comment/all/')
def showComments(restaurant_id):
    restaurant = session.query(Restaurant).get(restaurant_id)
    if restaurant_id == 0:
        complaints = session.query(Complaint).join(
            User).filter(User.id == Complaint.posted_by).all()
        recommendations = session.query(Recommendation).join(
            User).filter(User.id == Recommendation.posted_by).all()
    else:
        complaints = session.query(Complaint).join(User).filter(User.id == Complaint.posted_by).filter(
            Complaint.restaurant_id == restaurant_id).all()
        recommendations = session.query(Recommendation).join(User).filter(User.id == Recommendation.posted_by).filter(
            Recommendation.restaurant_id == restaurant_id).all()
    comments = {
        "complaints": complaints,
        "recommendations": recommendations
    }
    return render_template(
        'comments.html', comments=comments, restaurant=restaurant)


if __name__ == '__main__':
    app.debug = True
    app.run(host='0.0.0.0', port=5000)
