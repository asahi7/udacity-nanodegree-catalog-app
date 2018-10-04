from flask import Flask, request, session, redirect, flash, url_for, render_template, abort
from models.index import City, Base, Restaurant, User, Complaint, Recommendation
from sqlalchemy.orm import sessionmaker
from sqlalchemy import asc, create_engine
from flask_sqlalchemy import SQLAlchemy


app = Flask(__name__)
app.secret_key = "SECRET_KEY"
engine = create_engine("postgresql:///catalogdb")
Base.metadata.bind = engine
DBSession = sessionmaker(bind=engine)
session = DBSession()


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
        return render_template('newRestaurant.html')


@app.route('/city/<int:city_id>/restaurant/all/')
def showRestaurants(city_id):
    restaurants = session.query(Restaurant).filter_by(
        city_id=city_id).order_by(asc(Restaurant.name))
    return render_template(
        'restaurants.html', restaurants=restaurants, city_id=city_id)


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


@app.route("/restaurant/<int:restaurant_id>/comment/new/",
           methods=["GET", "POST"])
def newComment(restaurant_id):
    if request.method == "POST":
        if request.form["type"] == "complaint":
            complaint = Complaint(name=request.form["name"],
                                  description=request.form["description"],
                                  rate=int(request.form["rate"]),
                                  restaurant_id=restaurant_id,
                                  posted_by=1  # TODO: change when auth is added
                                  )
            session.add(complaint)
            flash(
                'New complaint `%s` in restaurant with id: %d was created' %
                (complaint.name, restaurant_id))
        elif request.form["type"] == "recommendation":
            recommendation = Recommendation(name=request.form["name"],
                                            description=request.form["description"],
                                            restaurant_id=restaurant_id,
                                            posted_by=1  # TODO: change when auth is added
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
        return render_template('newComment.html')


@app.route('/restaurant/<int:restaurant_id>/comment/all/')
def showComments(restaurant_id):
    complaints = session.query(Complaint).filter_by(
        restaurant_id=restaurant_id)
    recommendations = session.query(Recommendation).filter_by(
        restaurant_id=restaurant_id)
    comments = {
        "complaints": complaints,
        "recommendations": recommendations
    }
    return render_template(
        'comments.html', comments=comments, restaurant_id=restaurant_id)


if __name__ == '__main__':
    app.debug = True
    app.run(host='0.0.0.0', port=5000)
