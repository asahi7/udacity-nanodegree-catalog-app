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


def check_admin_access():
    if 'admin' in login_session and login_session['admin'] == True:
        return True
    return False


def check_user_access():
    if 'admin' in login_session and login_session['admin'] == False:
        return True
    return False


@app.route("/")
def showSignIn():
    return render_template("signin.html")


@app.route("/signin/user")
def showSignInUser():
    state = ''.join(random.choice(string.ascii_uppercase + string.digits)
                    for x in xrange(32))
    login_session['state'] = state
    loging_as_admin = False
    return render_template("login.html", STATE=state, as_admin=loging_as_admin)


@app.route("/signin/admin")
def showSignInAdmin():
    state = ''.join(random.choice(string.ascii_uppercase + string.digits)
                    for x in xrange(32))
    login_session['state'] = state
    loging_as_admin = True
    return render_template("login.html", STATE=state, as_admin=loging_as_admin)


def getUserData(credentials):
    userinfo_url = "https://www.googleapis.com/oauth2/v1/userinfo"
    params = {'access_token': credentials.access_token, 'alt': 'json'}
    answer = requests.get(userinfo_url, params=params)
    return answer.json()


def saveUserToDB(data, as_admin):
    username = data['name'] if 'name' in data else ''
    user = session.query(User).filter_by(email=data['email']).first()
    if user is None:
        user = User(
            name=username,
            email=data['email'],
            is_admin=as_admin)
        session.add(user)
        session.commit()
        flash('New user `%s` was created' % user.name)
    elif user.is_admin != as_admin:
        raise ValueError(
            'User has not a role with which he is trying to log in')
    login_session['username'] = username
    login_session['user_id'] = user.id
    login_session['email'] = data['email']
    login_session['admin'] = as_admin


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
    if request.args.get('as_admin') == 'True':
        as_admin = True
    else:
        as_admin = False
    try:
        saveUserToDB(data, as_admin)
    except ValueError as error:
        response = make_response(
            json.dumps(error.message), 401)
        response.headers['Content-Type'] = 'application/json'
        return response
    if stored_access_token is not None and gplus_id == stored_gplus_id:
        response = make_response(json.dumps('Current user is already connected.'),
                                 200)
        response.headers['Content-Type'] = 'application/json'
        return response
    login_session['access_token'] = credentials.access_token
    login_session['gplus_id'] = gplus_id
    return 'True'


@app.route('/gdisconnect')
def gdisconnect():
    if not check_admin_access() and not check_user_access():
        return redirect(url_for("showSignIn"))
    access_token = login_session.get('access_token')
    if access_token is None:
        print 'Access Token is None'
        response = make_response(
            json.dumps('Current user not connected.'), 401)
        response.headers['Content-Type'] = 'application/json'
        return response
    print 'In gdisconnect access token is %s' % access_token
    print 'User name is: '
    print login_session['username']
    url = 'https://accounts.google.com/o/oauth2/revoke?token=%s' % login_session['access_token']
    h = httplib2.Http()
    result = h.request(url, 'GET')[0]
    print 'result is '
    print result
    if result['status'] == '200':
        del login_session['access_token']
        del login_session['gplus_id']
        del login_session['username']
        del login_session['email']
        del login_session['admin']
        del login_session['user_id']
        return redirect(url_for('showSignIn'))
    else:
        response = make_response(
            json.dumps(
                'Failed to revoke token for given user.',
                400))
        response.headers['Content-Type'] = 'application/json'
        return response


@app.route("/city/new/", methods=["GET", "POST"])
def newCity():
    if not check_admin_access():
        return redirect(url_for('showSignIn'))
    if request.method == "POST":
        city = City(name=request.form["city"], country=request.form["country"])
        session.add(city)
        flash('New city `%s` was created' % city.name)
        session.commit()
        return redirect(url_for('showCities'))
    else:
        return render_template('newCity.html')


@app.route("/city/<int:city_id>/change/", methods=["POST", "GET"])
def changeCity(city_id):
    if not check_admin_access():
        return redirect(url_for('showSignIn'))
    city = session.query(City).get(city_id)
    if request.method == "POST":
        city.name = request.form["city"]
        city.country = request.form["country"]
        session.commit()
        return redirect(url_for('showCities'))
    else:
        return render_template('changeCity.html', city=city)


@app.route("/city/<int:city_id>/delete/", methods=["GET"])
def deleteCity(city_id):
    if not check_admin_access():
        return redirect(url_for('showSignIn'))
    city = session.query(City).get(city_id)
    if city is not None:
        session.delete(city)
        session.commit()
    return redirect(url_for('showCities'))


@app.route('/city/all/')
def showCities():
    if not check_admin_access() and not check_user_access():
        return redirect(url_for("showSignIn"))
    cities = session.query(City).order_by(asc(City.name))
    return render_template('cities.html', cities=cities)


@app.route("/city/<int:city_id>/restaurant/new/", methods=["GET", "POST"])
def newRestaurant(city_id):
    if not check_admin_access():
        return redirect(url_for("showSignIn"))
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


@app.route("/city/<int:city_id>/restaurant/<int:restaurant_id>/change/",
           methods=["POST", "GET"])
def changeRestaurant(city_id, restaurant_id):
    if not check_admin_access():
        return redirect(url_for('showSignIn'))
    restaurant = session.query(Restaurant).get(restaurant_id)
    city = session.query(City).get(city_id)
    if request.method == "POST":
        restaurant.name = request.form["name"]
        print request.form["description"]
        restaurant.description = request.form["description"]
        print restaurant.description
        session.commit()
        return redirect(url_for('showRestaurants', city_id=city_id))
    else:
        return render_template('changeRestaurant.html',
                               city=city, restaurant=restaurant)


@app.route('/city/<int:city_id>/restaurant/all/')
def showRestaurants(city_id):
    if not check_admin_access() and not check_user_access():
        return redirect(url_for("showSignIn"))
    city = session.query(City).get(city_id)
    if city_id == 0:
        restaurants = session.query(Restaurant).all()
    else:
        restaurants = session.query(Restaurant).filter_by(
            city_id=city_id).order_by(asc(Restaurant.name))
    return render_template(
        'restaurants.html', restaurants=restaurants, city=city)


@app.route('/user/all/')
def showUsers():
    if not check_admin_access() and not check_user_access():
        return redirect(url_for("showSignIn"))
    users = session.query(User)
    return render_template('users.html', users=users)


@app.route('/user/<int:user_id>/')
def showUser(user_id):
    if not check_admin_access() and not check_user_access():
        return redirect(url_for("showSignIn"))
    user = session.query(User).get(user_id)
    return render_template('user.html', user=user)


@app.route("/restaurant/<int:restaurant_id>/comment/new/",
           methods=["GET", "POST"])
def newComment(restaurant_id):
    if not check_user_access():
        return redirect(url_for("showSignIn"))
    if request.method == "POST":
        if request.form["type"] == "complaint":
            complaint = Complaint(name=request.form["name"],
                                  description=request.form["description"],
                                  rate=int(request.form["rate"]),
                                  restaurant_id=restaurant_id,
                                  posted_by=login_session['user_id']
                                  )
            session.add(complaint)
            flash(
                'New complaint `%s` in restaurant with id: %d was created' %
                (complaint.name, restaurant_id))
        elif request.form["type"] == "recommendation":
            recommendation = Recommendation(name=request.form["name"],
                                            description=request.form["description"],
                                            restaurant_id=restaurant_id,
                                            posted_by=login_session['user_id']
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
    if not check_admin_access() and not check_user_access():
        return redirect(url_for("showSignIn"))
    restaurant = session.query(Restaurant).get(restaurant_id)
    if restaurant_id == 0:
        complaints = session.query(Complaint).join(
            User).join(Restaurant).filter(Restaurant.id == Complaint.restaurant_id).filter(User.id == Complaint.posted_by).all()
        recommendations = session.query(Recommendation).join(
            User).join(Restaurant).filter(Restaurant.id == Recommendation.restaurant_id).filter(User.id == Recommendation.posted_by).all()
    else:
        complaints = session.query(Complaint).join(User).join(Restaurant).filter(Restaurant.id == Complaint.restaurant_id).filter(User.id == Complaint.posted_by).filter(
            Complaint.restaurant_id == restaurant_id).all()
        recommendations = session.query(Recommendation).join(User).join(Restaurant).filter(Restaurant.id == Recommendation.restaurant_id).filter(User.id == Recommendation.posted_by).filter(
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
