from flask import Flask
from model import db  # Κρατάμε το δικό σου όνομα αρχείου όπως είναι!

app = Flask(__name__)

# Ρυθμίσεις Βάσης Δεδομένων
app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///games.db'
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False

# Αρχικοποίηση της βάσης
db.init_app(app)

if __name__ == '__main__':
    # Μεταφέρουμε τα routes ΕΔΩ μέσα για να μην μπερδεύεται η Flask
    from routes import main
    app.register_blueprint(main)

    with app.app_context():
        db.create_all() # Δημιουργία της βάσης δεδομένων
        
    app.run(debug=True, port=8080)
