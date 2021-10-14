from myproject import db, login_manager
from flask_bcrypt import generate_password_hash, check_password_hash
from flask_login import UserMixin
from datetime import datetime


@login_manager.user_loader
def load_user(user_id):
    return User.query.get(user_id)


class User(db.Model, UserMixin):
    __tablename__ = 'users'

    id = db.Column(db.Integer, primary_key=True)
    email = db.Column(db.String(64), unique=True, index=True)
    username = db.Column(db.String(64), unique=True, index=True)
    user_bio = db.Column(db.String)
    profile_image = db.Column(db.String(20), default='default_profile.png')
    password_hash = db.Column(db.String(128))
    # Build Reviews Relationship with User
    review_post = db.relationship('Reviews', backref='author', lazy=True)
    # Build Watchlist Relationship with User
    watchlist_user = db.relationship('Watchlist', backref='author', lazy=True)

    def __init__(self, email, username, password):
        self.email = email
        self.username = username
        self.password_hash = generate_password_hash(password)

    def check_password(self, password):
        return check_password_hash(self.password_hash, password)

    def __repr__(self):
        return f"UserName: {self.username}"


class Reviews(db.Model):
    # Setup the relationship to the User table
    users = db.relationship(User)

    # Model for the Review Posts on Website
    review_id = db.Column(db.Integer, primary_key=True)
    # connect review to a particular author
    user_id = db.Column(db.Integer, db.ForeignKey('users.id'), nullable=False)
    review_date = db.Column(db.DateTime, nullable=False, default=datetime.utcnow)
    movie_title = db.Column(db.String(140), nullable=False)
    movie_id = db.Column(db.Integer, nullable=False)
    review_text = db.Column(db.Text, nullable=False)

    def __init__(self, movie_title, review_text, movie_id, user_id):
        self.movie_title = movie_title
        self.movie_id = movie_id
        self.review_text = review_text
        self.user_id = user_id

    def __repr__(self):
        return f"Post Id: {self.review_id} --- Date: {self.review_date} --- Title: {self.movie_title}"


class Watchlist(db.Model):
    users = db.relationship(User)

    watchlist_id = db.Column(db.Integer, primary_key=True)
    # connect review to a particular author
    user_id = db.Column(db.Integer, db.ForeignKey('users.id'), nullable=False)
    movie_id = db.Column(db.Integer, nullable=False)
    watched = db.Column(db.Boolean, default=False)

    def __init__(self, user_id, movie_id):
        self.user_id = user_id
        self.movie_id = movie_id

