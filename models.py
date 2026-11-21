
from extensions import db


class User(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(100), nullable=False)
    email = db.Column(db.String(120), unique=True, nullable=False)
    headline = db.Column(db.String(150), default="")


class Profile(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(100), nullable=False)
    skills = db.Column(db.JSON, nullable=False)
    specialization = db.Column(db.String(150), default="")
    bio = db.Column(db.Text, default="")
