from flask_sqlalchemy import SQLAlchemy
from flask_login import UserMixin

db = SQLAlchemy()

# πινακας για τους χρήστες
class User(db.Model, UserMixin):
    id = db.Column(db.Integer, primary_key=True) # Μοναδικό ID για τη βάση μας
    username = db.Column(db.String(50), unique=True, nullable=False) # Όνομα χρήστη
    email = db.Column(db.String(120), unique=True, nullable=False) # Email χρήστη
    password_hash = db.Column(db.String(256), nullable=False) # Κωδικός χρήστη

    favorites = db.relationship('FavoriteGame', backref='user', lazy=True) # Σχέση με τα αγαπημένα παιχνίδια
    

class FavoriteGame(db.Model):
    id = db.Column(db.Integer, primary_key=True) # Μοναδικό ID για τη βάση μας
    rawg_id = db.Column(db.String(50), nullable=False)
    name = db.Column(db.String(100), nullable=False) # Όνομα παιχνιδιού
    image = db.Column(db.String(255)) # Link εικόνας

    user_id = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=False) # Σχέση με τον χρήστη