from sqlalchemy import Column, ForeignKey, Integer, String, Text, Boolean, DateTime
from sqlalchemy.ext.declarative import declarative_base
from datetime import datetime
from sqlalchemy.orm import relationship


Base = declarative_base()


class City(Base):
    __tablename__ = 'city'

    id = Column(Integer, primary_key=True)
    name = Column(String(120), nullable=False)
    country = Column(String(120), nullable=False)
    restaurants = relationship('Restaurant', backref='city', passive_deletes=True, lazy=True)

    def __repr__(self):
        return '<City %r at %r>' % (self.name, self.country)


class Restaurant(Base):
    __tablename__ = 'restaurant'

    id = Column(Integer, primary_key=True)
    name = Column(String(120), nullable=False)
    description = Column(Text, nullable=False)
    city_id = Column(Integer, ForeignKey('city.id', ondelete='CASCADE'), nullable=False)
    complaints = relationship('Complaint', backref='restaurant', passive_deletes=True, lazy=True)
    recommendations = relationship(
        'Recommendation', backref='restaurant', passive_deletes=True, lazy=True)

    def __repr__(self):
        return '<Restaurant %r>' % (self.name)


class Complaint(Base):
    __tablename__ = 'complaint'

    id = Column(Integer, primary_key=True)
    name = Column(String(120), nullable=False)
    description = Column(Text, nullable=False)
    rate = Column(Integer, nullable=False)
    restaurant_id = Column(
        Integer,
        ForeignKey('restaurant.id', ondelete='CASCADE'),
        nullable=False)
    posted_date = Column(
        DateTime,
        nullable=False,
        default=datetime.utcnow)
    posted_by = Column(Integer, ForeignKey('user.id'), nullable=False)

    def __repr__(self):
        return '<Complaints %r with rate %d>' % (self.name, self.rate)


class Recommendation(Base):
    __tablename__ = 'recommendation'

    id = Column(Integer, primary_key=True)
    name = Column(String(120), nullable=False)
    description = Column(Text, nullable=False)
    restaurant_id = Column(
        Integer,
        ForeignKey('restaurant.id', ondelete='CASCADE'),
        nullable=False)
    posted_date = Column(
        DateTime,
        nullable=False,
        default=datetime.utcnow)
    posted_by = Column(Integer, ForeignKey('user.id'), nullable=False)

    def __repr__(self):
        return '<Recommendation %r>' % (self.name)


class User(Base):
    __tablename__ = 'user'

    id = Column(Integer, primary_key=True)
    name = Column(String(120), nullable=False)
    email = Column(String(120), nullable=False)
    is_admin = Column(Boolean, nullable=False)
    complaints = relationship('Complaint', backref='user', lazy=True)
    recommendations = relationship(
        'Recommendation', backref='user', lazy=True)

    def __repr__(self):
        return '<User %r>' % (self.name)
