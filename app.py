import sys
import os

# Χρησιμοποιεί το pg8000 τοπικά στο laptop, αλλά το προσπερνάει στο Render
try:
    import pg8000.dbapi
    sys.modules['psycopg2'] = pg8000.dbapi
    print("Local environment detected: Using pg8000 driver.", flush=True)
except ImportError:
    print("Production enviroment detected: Using native psycopg2 driver.", flush=True)

basedir = os.path.abspath(os.path.dirname(__file__))
load_dotenv_path = os.path.join(basedir, '.env')

from dotenv import load_dotenv
load_dotenv(load_dotenv_path)

from flask import Flask
from flask_login import LoginManager
from model import User, db  # Κρατάμε το δικό σου όνομα αρχείου όπως είναι!
from flask_migrate import Migrate
from flask_mail import Mail, Message 

app = Flask(__name__)

app.config['MAIL_SERVER'] = 'smtp.gmail.com'
app.config['MAIL_PORT'] = 587
app.config['MAIL_USE_TLS'] = True
app.config['MAIL_USE_SSL'] = False
app.config['MAIL_USERNAME'] = 'mygamesreviewhub@gmail.com'
app.config['MAIL_PASSWORD'] = os.environ.get('MAIL_PASSWORD')
app.config['MAIL_DEFAULT_SENDER'] = 'mygamesreviewhub@gmail.com'

mail = Mail(app)

migrate = Migrate(app, db)

# Αυτόματη μετατροπή του driver σε pg8000 για να παρακαμφθεί το App Control των Windows
raw_db_url = os.environ.get('DATABASE_URL')
if raw_db_url:
    if raw_db_url and raw_db_url.startswith('postgresql://'):
        raw_db_url = raw_db_url.replace('postgresql://', 'postgresql+pg8000://', 1)
    elif raw_db_url and raw_db_url.startswith('postgresql+psycopg2://'):
        raw_db_url = raw_db_url.replace('postgresql+psycopg2://', 'postgresql+pg8000://', 1)

app.config['SQLALCHEMY_DATABASE_URI'] = raw_db_url
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False


app.config['SECRET_KEY'] = 'your-secret-key'  # Προσθέστε ένα secret key
login_manager = LoginManager()
login_manager.init_app(app)
login_manager.login_view = 'main.login'


@login_manager.user_loader
def load_user(user_id):
    return User.query.get(int(user_id))

# Ρυθμίσεις Βάσης Δεδομένων
#database_url = os.environ.get('DATABASE_URL', 'postgresql://postgres.hhelzbmfquwexrrickiq:ultrastudent516%40d@aws-1-eu-west-1.pooler.supabase.com:6543/postgres')

#if database_url and database_url.startswith("postgres://"):
    database_url = database_url.replace("postgres://", "postgresql://", 1)

#app.config['SQLALCHEMY_DATABASE_URI'] = database_url
#app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False


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
