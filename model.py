from flask_sqlalchemy import SQLAlchemy 

db = SQLAlchemy()

class FavoriteGame(db.Model):
    id = db.Column(db.Integer, primary_key=True) # Μοναδικό ID για τη βάση μας
    rawg_id = db.Column(db.Integer, unique=True, nullable=False) # Το ID από το API της RAWG
    name = db.Column(db.String(100), nullable=False) # Όνομα παιχνιδιού
    image = db.Column(db.String(255)) # Link εικόνας

    def __repr__(self):
        return f'<Game {self.name}>'
