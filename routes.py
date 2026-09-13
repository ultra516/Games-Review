import requests
from flask import Blueprint, render_template, request, redirect, url_for
from model import FavoriteGame, db

main = Blueprint('main', __name__)

API_KEY = 'cd1ef211106a40888b22f4e2b284b9a6'

@main.route('/')
def home():

    search_query = request.args.get('search')
    games_data = []

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

    return render_template('games.html', games=games_data)

@main.route('/game/<int:game_id>')
def game_details(game_id):
    detail_url = f'https://api.rawg.io/api/games/{game_id}?key={API_KEY}'
    detail_response = requests.get(detail_url)
    game_data = detail_response.json()

    # Fetch screenshots for the game
    screenshots_url = f'https://api.rawg.io/api/games/{game_id}/screenshots?key={API_KEY}'
    screenshots_response = requests.get(screenshots_url)
    screenshots = screenshots_response.json().get('results', [])

    return render_template('details.html', game=game_data, screenshots=screenshots)

@main.route('/favorite/add', methods=['POST'])
def add_favorite():
    game_id = request.form.get('game_id')
    game_name = request.form.get('game_name')
    game_image = request.form.get('game_image')

    # Έλεγχος αν υπάρχει ήδη στα αγαπημένα για να μην διπλογραφτεί
    exists = FavoriteGame.query.filter_by(rawg_id=game_id).first()
    if not exists:
        new_favorite = FavoriteGame(rawg_id=game_id, name=game_name, image=game_image)
        db.session.add(new_favorite)
        db.session.commit()  # Αποθήκευση στη βάση δεδομένων

    return redirect(url_for('main.home'))

# 2. READ: Εμφάνιση όλων των Αγαπημένων παιχνιδιών
@main.route('/favorites')
def show_favorites():
    # Παίρνουμε όλα τα παιχνίδια από τη βάση δεδομένων
    fav_games = FavoriteGame.query.all()
    return render_template('favorites.html', favorite_games=fav_games)

@main.route('/favorite/delete/<int:fav_id>', methods=['POST'])
def delete_favorite(fav_id):
    # Ψάχνει το παιχνίδι στη βάση με βάση το ID του. Αν δεν το βρει, βγάζει 404.
    game_to_delete = FavoriteGame.query.get_or_404(fav_id)
    db.session.delete(game_to_delete)
    db.session.commit()  # Οριστική αφαίρεση από το games.db
    return redirect(url_for('main.show_favorites'))