from flask_login import login_user, logout_user, login_required, current_user
import requests
from flask import Blueprint, render_template, request, redirect, url_for, flash
from model import FavoriteGame, db, User
from werkzeug.security import generate_password_hash, check_password_hash
from urllib.parse import quote


main = Blueprint('main', __name__)

API_KEY = 'cd1ef211106a40888b22f4e2b284b9a6'

@main.route('/')
def home():

    search_query = request.args.get('search')
    games_data = []
    favorite_ids = []
    if current_user.is_authenticated:
        favs = FavoriteGame.query.filter_by(user_id=current_user.id).all()
        favorite_ids = [str(fav.rawg_id) for fav in favs]  # Μετατροπή σε string για σύγκριση
    try:
        if search_query:
            response = requests.get(f'https://api.rawg.io/api/games?search={search_query}&key={API_KEY}', timeout=3)
            games_data = response.json().get('results', [])
        else:
            # Αν δεν υπάρχει αναζήτηση, φέρε τα 10 πιο δημοφιλή παιχνίδια
            response = requests.get(f'https://api.rawg.io/api/games?ordering=-popularity&key={API_KEY}', timeout=3)
            games_data = response.json().get('results', [])
    except requests.RequestException:
        games_data = []

    return render_template('games.html', games=games_data,favorite_ids=favorite_ids)

@main.route('/game/<game_id>')
def game_details(game_id):
    detail_url = f'https://api.rawg.io/api/games/{game_id}?key={API_KEY}'
    detail_response = requests.get(detail_url)
    game_data = detail_response.json()

    # Fetch screenshots for the game
    screenshots_url = f'https://api.rawg.io/api/games/{game_id}/screenshots?key={API_KEY}'
    screenshots_response = requests.get(screenshots_url)
    screenshots = screenshots_response.json().get('results', [])

    is_favorite = False
    current_alert_price = None

    if current_user.is_authenticated:
        try:
            safe_id = str(game_id)  # Προσπαθούμε να μετατρέψουμε το game_id σε string
            exists = FavoriteGame.query.filter_by(rawg_id=safe_id, user_id=current_user.id).first()
            if exists:
                is_favorite = True
                current_alert_price = exists.target_price  # Παίρνουμε την τρέχουσα τιμή ειδοποίησης
        except (ValueError, TypeError):
            pass  # Αν το game_id δεν είναι έγκυρο ακέραιο, αγνοούμε το λάθος

    deals = []
    try:
        # Αρχικοποιούμε τη μεταβλητή αμέσως για να υπάρχει ΠΑΝΤΑ στη μνήμη
       
        game_name = game_data.get('name')

        if game_name:
            # Αφαιρούμε τα σύμβολα (όπως :, -, !) που μπερδεύουν το CheapShark
            clean_name = game_name.replace(':', '').replace('-', ' ').replace('!', '')  
            # Αφαιρούμε τυχόν διπλά κενά διαστήματα που δημιουργήθηκαν
            clean_name = " ".join(clean_name.split())

            # Κωδικοποίηση του ονόματος για το URL
            safe_game_name = quote(clean_name)  

             # ΟΡΙΖΟΥΜΕ ΤΟ CUSTOM USER-AGENT ΟΠΩΣ ΖΗΤΑΕΙ ΤΟ CHEAPSHARK DOCUMENTATION
            headers = {
                'User-Agent': 'GamesReviewHub/1.0 (contact@gamesreviewhub.com)'
            }

            # Ψάχνουμε το παιχνίδι στο CheapShark με βάση το όνομά του
            search_res= requests.get(f'https://www.cheapshark.com/api/1.0/games?title={safe_game_name}&limit=1', headers=headers, timeout=3)
            search_data = search_res.json()

            #Αν δεν βρει τίποτα με ολόκληρο το όνομα, δοκιμάζει με τις 3 πρώτες λέξεις
            if not search_data or len(search_data) == 0:
                words = clean_name.split()
                if len(words) > 3:
                    short_name = " ".join(words[:3])
                    search_res = requests.get(f'https://www.cheapshark.com/api/1.0/games?title={quote(short_name)}&limit=1', headers=headers, timeout=3)
                    search_data = search_res.json()
                    print("--- CHEAPSHARK DEBUG START ---")
                    print(f"Cleaned Title: {clean_name}")
                    print(f"API Response: {search_data}")

            # Ελέγχουμε με ασφάλεια αν η λίστα έχει στοιχεία πριν διαβάσουμε τη θέση [0]
            if search_data and isinstance(search_data, list) and len(search_data) > 0:
                cheapshark_game_id = search_data[0].get('gameID')

                if cheapshark_game_id:
                    # Ζητάμε όλες τις live προσφορές και τα stores για αυτό το ID
                    prices_res = requests.get(f'https://www.cheapshark.com/api/1.0/games?id={cheapshark_game_id}', headers=headers, timeout=3)
                    prices_data = prices_res.json()
                    deals = prices_data.get('deals', [])

    except Exception as e:
        print(f"CheapShark Error: {e}")
        deals = [] # Αν πέσει το API, η σελίδα θα συνεχίσει να ανοίγει κανονικά    

        
    # ΛΕΞΙΚΟ ΚΑΤΑΣΤΗΜΑΤΩΝ (ΚΑΛΥΠΤΕΙ ΟΛΟ ΤΟ CHEAPSHARK API)
    store_names = {
        "1": "Steam",
        "2": "GamersGate",
        "3": "GreenManGaming",
        "4": "Amazon",
        "5": "GameStop",
        "6": "Direct2Drive",
        "7": "GOG",
        "8": "Origin",
        "9": "Get Games",
        "10": "Shiny Loot",
        "11": "Epic Games Store",
        "12": "IndieGameStand",
        "13": "Digital Download",
        "14": "Bundle Stars",
        "15": "SilaGames",
        "16": "Squirt創意遊戲",
        "17": "Playfield",
        "18": "Imperial Games",
        "19": "WinGameStore",
        "20": "Funstock Digital",
        "21": "GameBillet",
        "22": "Voidu",
        "23": "Humble Store",
        "24": "MacGameStore",
        "25": "Fanatical",
        "26": "Gamesrocket",
        "27": "Gamesplanet",
        "28": "Xsolla Store",
        "29": "IndieGala",
        "30": "Blizzard Shop",
        "31": "AllYouPlay",
        "32": "DLGamer",
        "33": "Noctre",
        "34": "Nintendo eShop",
        "35": "Origin / EA App"
    }


   

   
    return render_template('details.html', game=game_data, screenshots=screenshots, is_favorite=is_favorite, deals=deals, store_names=store_names, current_alert_price=current_alert_price)

    

@main.route('/favorite/add', methods=['POST'])
def add_favorite():
    if not current_user.is_authenticated:
        
        return redirect(url_for('main.login'))
    game_id = request.form.get('game_id')
    game_name = request.form.get('game_name')
    game_image = request.form.get('game_image')

    # Έλεγχος αν υπάρχει ήδη στα αγαπημένα για να μην διπλογραφτεί
    exists = FavoriteGame.query.filter_by(rawg_id=game_id, user_id=current_user.id).first()
    if not exists:
        new_favorite = FavoriteGame(rawg_id=game_id, name=game_name, image=game_image, user_id=current_user.id)
        db.session.add(new_favorite)
        db.session.commit()  # Αποθήκευση στη βάση δεδομένων
        flash(f'Το παιχνίδι "{game_name}" προστέθηκε με επιτυχία στα αγαπημένα σας!', 'success')
    else:
        flash(f'Το παιχνίδι "{game_name}" υπάρχει ήδη στα αγαπημένα σας.', 'info')
    return redirect(url_for('main.home'))

# 2. READ: Εμφάνιση όλων των Αγαπημένων παιχνιδιών
@main.route('/favorites')
def show_favorites():
    if not current_user.is_authenticated:
        flash('Πρέπει να είστε συνδεδεμένος για να δείτε τα αγαπημένα σας παιχνίδια.', 'warning')
        return redirect(url_for('main.login'))
    fav_games = FavoriteGame.query.filter_by(user_id=current_user.id).all()
    return render_template('favorites.html', favorite_games=fav_games)

@main.route('/favorite/delete/<int:fav_id>', methods=['POST'])
def delete_favorite(fav_id):
    # Ψάχνει το παιχνίδι στη βάση με βάση το ID του. Αν δεν το βρει, βγάζει 404.
    game_to_delete = FavoriteGame.query.get_or_404(fav_id)
    db.session.delete(game_to_delete)
    db.session.commit()  # Οριστική αφαίρεση από το games.db
    return redirect(url_for('main.show_favorites'))

@main.route('/register', methods=['GET', 'POST'])
def register():
    if request.method == 'POST':
        username = request.form.get('username')
        email = request.form.get('email')
        password = request.form.get('password')

        # Ελέγχουμε αν ο χρήστης υπάρχει ήδη
        if User.query.filter_by(email=email).first():
            return render_template('register.html', error='Ο χρήστης με αυτό το email υπάρχει ήδη.')

        # Έλεγχος αν το username υπάρχει ήδη
        if User.query.filter_by(username=username).first():
            return render_template('register.html', error='Αυτό το όνομα χρήστη χρησιμοποιείται ήδη.')

        hashed_password = generate_password_hash(password, method='pbkdf2:sha256')

        # Δημιουργούμε τον νέο χρήστη
        new_user = User(username=username, email=email, password_hash=hashed_password)
        db.session.add(new_user)
        db.session.commit()

        return redirect(url_for('main.login'))

    return render_template('register.html')

@main.route('/login', methods=['GET', 'POST'])
def login():
    if request.method == 'POST':
        email = request.form.get('email')
        password = request.form.get('password')

        user = User.query.filter_by(email=email).first()

        if user and check_password_hash(user.password_hash, password):
            login_user(user)
            
            return redirect(url_for('main.home'))

    return render_template('login.html')

@main.route('/logout')
@login_required
def logout():
    logout_user()
    flash('Έχεις αποσυνδεθεί επιτυχώς.', 'info')
    return redirect(url_for('main.home'))

@main.route('/delete_account', methods=['POST'])
@login_required
def delete_account():
    user_to_delete = current_user
    FavoriteGame.query.filter_by(user_id=user_to_delete.id).delete()  # Διαγραφή των αγαπημένων του χρήστη
    db.session.delete(user_to_delete)
    db.session.commit()
    logout_user()  # Αποσύνδεση του χρήστη μετά τη διαγραφή
    flash('Ο λογαριασμός σας και όλα τα δεδομένα σας διαγράφηκαν επιτυχώς.', 'info')
    return redirect(url_for('main.home'))

@main.route('/favorites/set_alert', methods=['POST'])
@login_required
def set_price_alert():
    game_id = request.form.get('game_id')
    target_price = request.form.get('target_price')
    favorite_game = FavoriteGame.query.filter_by(rawg_id=str(game_id), user_id=current_user.id).first()

    if favorite_game: 
        try:
            favorite_game.target_price = float(target_price)
            db.session.commit()
            flash(f'Ο στόχος τιμής για το "{favorite_game.name}" ορίστηκε στα {target_price}€.', 'success')
        except ValueError:
            flash('Παρακαλώ εισάγετε μια έγκυρη τιμή.', 'danger')
    else:
        flash('Το παιχνίδι δεν βρέθηκε στα αγαπημένα.', 'danger')

    return redirect(url_for('main.game_details', game_id=game_id))