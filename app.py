import os

from flask import Flask
from flask_login import LoginManager
from model import User, db  # Κρατάμε το δικό σου όνομα αρχείου όπως είναι!

app = Flask(__name__)

app.config['SECRET_KEY'] = 'your-secret-key'  # Προσθέστε ένα secret key
login_manager = LoginManager()
login_manager.init_app(app)
login_manager.login_view = 'main.login'


@login_manager.user_loader
def load_user(user_id):
    return User.query.get(int(user_id))

# Ρυθμίσεις Βάσης Δεδομένων
database_url = os.environ.get('DATABASE_URL', 'postgresql://postgres.hhelzbmfquwexrrickiq:ultrastudent516%40d@aws-1-eu-west-1.pooler.supabase.com:6543/postgres')

if database_url and database_url.startswith("postgres://"):
    database_url = database_url.replace("postgres://", "postgresql://", 1)

app.config['SQLALCHEMY_DATABASE_URI'] = database_url
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False


# Αρχικοποίηση της βάσης
db.init_app(app)

if __name__ == '__main__':
    # Μεταφέρουμε τα routes ΕΔΩ μέσα για να μην μπερδεύεται η Flask
    from routes import main
    app.register_blueprint(main)

    with app.app_context():
        db.create_all() # Δημιουργία της βάσης δεδομένων
        
    # Παίρνει τη θύρα που του δίνει το Render, αλλιώς τοπικά κρατάει την 8080
    port = int(os.environ.get("PORT", 8080))
    app.run(host="0.0.0.0", port=port)
