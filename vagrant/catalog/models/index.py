from flask import Flask
from flask_sqlalchemy import SQLAlchemy
from datetime import datetime

app = Flask(__name__)
app.config['SQLALCHEMY_DATABASE_URI'] = 'postgresql:///catalogdb'
db = SQLAlchemy(app)


class City(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(120), nullable=False)
    country = db.Column(db.String(120), nullable=False)
    restaurants = db.relationship('Restaurant', backref='city', lazy=True)

    def __repr__(self):
        return '<City %r at %r>' % (self.name, self.country)


class Restaurant(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(120), nullable=False)
    description = db.Column(db.Text, nullable=False)
    city_id = db.Column(db.Integer, db.ForeignKey('city.id'), nullable=False)
    complaints = db.relationship('Complaint', backref='restaurant', lazy=True)
    recommendations = db.relationship(
        'Recommendation', backref='restaurant', lazy=True)

    def __repr__(self):
        return '<Restaurant %r>' % (self.name)


class Complaint(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(120), nullable=False)
    description = db.Column(db.Text, nullable=False)
    rate = db.Column(db.Integer, nullable=False)
    restaraunt_id = db.Column(
        db.Integer,
        db.ForeignKey('restaurant.id'),
        nullable=False)
    posted_date = db.Column(
        db.DateTime,
        nullable=False,
        default=datetime.utcnow)
    posted_by = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=False)

    def __repr__(self):
        return '<Complaints %r with rate %d>' % (self.name, self.rate)


class Recommendation(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(120), nullable=False)
    description = db.Column(db.Text, nullable=False)
    restaraunt_id = db.Column(
        db.Integer,
        db.ForeignKey('restaurant.id'),
        nullable=False)
    posted_date = db.Column(
        db.DateTime,
        nullable=False,
        default=datetime.utcnow)
    posted_by = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=False)

    def __repr__(self):
        return '<Recommendation %r>' % (self.name)


class User(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(120), nullable=False)
    email = db.Column(db.String(120), nullable=False)
    is_admin = db.Column(db.Boolean, nullable=False)
    complaints = db.relationship('Complaint', backref='user', lazy=True)
    recommendations = db.relationship(
        'Recommendation', backref='user', lazy=True)

    def __repr__(self):
        return '<User %r>' % (self.name)
