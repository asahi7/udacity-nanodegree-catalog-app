from flask import Flask, request, session, redirect, flash, url_for, render_template
from models.index import City, Base
from sqlalchemy.orm import sessionmaker
from sqlalchemy import asc, create_engine


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


if __name__ == '__main__':
    app.debug = True
    app.run(host='0.0.0.0', port=5000)
