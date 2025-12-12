from flask import Flask, render_template, request, url_for, send_from_directory, flash, redirect, session
from flask_wtf import FlaskForm
from wtforms import StringField, URLField, RadioField, FileField, SubmitField, PasswordField
from wtforms.validators import DataRequired, URL, EqualTo
from werkzeug.utils import secure_filename
from flask_wtf.file import FileAllowed
from tasks.scheduler import start_scheduler
from flask_bcrypt import Bcrypt
from flask_login import LoginManager, UserMixin, current_user, login_user, logout_user, login_required

import os
import sqlite3


app = Flask(__name__, template_folder='./static/templates')
app.config['SECRET_KEY'] = '2ah!gh27#g40s5w5&-5f0ehjr@$&'  # For CSRF protection
app.config['UPLOAD_FOLDER'] = os.path.join('static', 'covers')
app.config['MAX_CONTENT_LENGTH'] = 16 * 1024 * 1024
app.config['BASE_DATA_PATH'] = os.path.abspath(os.path.join(os.path.dirname(__file__), '../../../../data/'))
bcrypt = Bcrypt(app)
login_manager = LoginManager(app)

# The path where comics are stored
path = app.config['BASE_DATA_PATH']

# Define comic add form
class AddForm(FlaskForm):
    title = StringField('title', validators=[DataRequired()])
    url = URLField('url', validators=[DataRequired(), URL()])
    language = RadioField('language', choices=[('english', 'English'), ('korean', 'Korean')], validators=[DataRequired()])
    cover_image = FileField('cover_image', validators=[
        FileAllowed(['jpg', 'png', 'jpeg'], 'Images only!')
    ])
    submit = SubmitField('submit')

# Define user add form
class UserForm(FlaskForm):
    username = StringField('username', validators=[DataRequired()])
    password = PasswordField('password', validators=[DataRequired()])
    confirm_password = PasswordField('confirm_password', validators=[DataRequired(), EqualTo('password')])
    register = SubmitField('register')

# Define login form
class LoginForm(FlaskForm):
    username = StringField('username', validators=[DataRequired()])
    password = PasswordField('password', validators=[DataRequired()])
    login = SubmitField('login')

class User(UserMixin):
    def __init__(self, id, username, password):
        self.id = id
        self.username = username
        self.password = password


@login_manager.user_loader
def load_user(user_id):
    with sqlite3.connect('./db/webtoons.db') as conn:
        cursor = conn.cursor()
        user = cursor.execute('SELECT * FROM users WHERE id = ?', (user_id,)).fetchone()
        if user:
            return User(id=user[0], username=user[1], password=user[2])
    return None


def init_db():
    db_path = os.path.abspath(os.path.join(os.path.dirname(__file__), 'db'))

    # Make the path for the directory if it doesn't exist yet
    if not os.path.isdir(db_path):
        os.mkdir(db_path)

    with sqlite3.connect('./db/webtoons.db') as conn:
        cursor = conn.cursor()
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS comics (
                id INTEGER PRIMARY KEY,
                title TEXT UNIQUE NOT NULL,
                url TEXT UNIQUE NOT NULL,
                language TEXT NOT NULL,
                cover_image TEXT
            )
        ''')
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS users (
                id INTEGER PRIMARY KEY,
                username TEXT UNIQUE NOT NULL,
                password TEXT NOT NULL
            )
        ''')
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS bookmarks (
                id INTEGER PRIMARY KEY,
                user_id INTEGER,
                language TEXT NOT NULL,
                comic_title TEXT NOT NULL,
                episode TEXT NOT NULL,
                FOREIGN KEY(user_id) REFERENCES users(id) ON DELETE CASCADE,
                UNIQUE (user_id, language, comic_title, episode)
            )
        ''')
        conn.commit()


# Add an episode bookmark for a specific user
def add_bookmark(user_id, language, comic_title, episode):
    try:    
        with sqlite3.connect('./db/webtoons.db') as conn:
            cursor = conn.cursor()
            cursor.execute('INSERT INTO bookmarks (user_id, language, comic_title, episode) VALUES (?, ?, ?, ?)', (user_id, language, comic_title, episode,))
            conn.commit()
    except Exception as e:
        print(f'Trouble adding bookmark. Exception: {e}')


# Remove an episode bookmark for a specific user
def remove_bookmark(user_id, language, comic_title, episode):
    try:    
        with sqlite3.connect('./db/webtoons.db') as conn:
            cursor = conn.cursor()
            cursor.execute('DELETE FROM bookmarks WHERE user_id = ? AND language = ? AND comic_title = ? AND episode = ?', (user_id, language, comic_title, episode,))
            conn.commit()
            print('Bookmark removed successfully.')
    except Exception as e:
        print(f'Trouble removing bookmark. Exception: {e}')


# Retrieve a user's bookmarks
def get_bookmarks(user_id):
    try:
        with sqlite3.connect('./db/webtoons.db') as conn:
            cursor = conn.cursor()
            cursor.execute('SELECT * FROM bookmarks WHERE user_id = ?', (user_id,))
            results = cursor.fetchall()
            bookmarks = []
            for row in results:
                bookmark = {
                    'id': row[0],
                    'user_id': row[1],
                    'language': row[2],
                    'comic_title': row[3],
                    'episode': row[4]
                }
                bookmarks.append(bookmark)
            return bookmarks
    except Exception as e:
        print(f'Trouble fetching bookmarks. Exception: {e}')


# Retrieve a single bookmark
def get_bookmark(user_id, language, comic, episode):
    try:
        with sqlite3.connect('./db/webtoons.db') as conn:
            cursor = conn.cursor()
            cursor.execute('SELECT * FROM bookmarks WHERE user_id = ? AND language = ? AND comic_title = ? AND episode = ?', (user_id, language, comic, episode))
            result = cursor.fetchone()
            bookmark = {
                'id': result[0],
                'user_id': result[1],
                'comic_title': result[2],
                'episode': result[3]
            }
            return bookmark
        
    except Exception as e:
        print(f'Trouble fetching bookmark. Exception: {e}')


# Toggle bookmark action
def toggle_bookmark():
    ...


# Injects user authentication status into the app context for templates
@app.context_processor
def inject_user_auth():
    return {'user_authenticated': current_user.is_authenticated}

# App route views
@app.route('/register', methods=['GET', 'POST'])
def register():
    form = UserForm()

    if form.validate_on_submit():
        username = form.username.data
        password = form.password.data
        hashed_password = bcrypt.generate_password_hash(password).decode('utf-8')

        try:
            with sqlite3.connect('./db/webtoons.db') as conn:
                cursor = conn.cursor()
                cursor.execute('''
                    INSERT INTO users (username, password)
                    VALUES (?, ?)    
                ''', (username, hashed_password,))
                conn.commit()

            # Show success message
            flash(f'{username} Added Successfully!', 'success')
        except Exception as e:
            print(f'Trouble adding {username}. Exception: {e}')

    return render_template('register.html', form=form)

@app.route('/login', methods=['GET', 'POST'])
def login():
    form = LoginForm()
    if form.validate_on_submit():
        username = form.username.data
        password = form.password.data

        try:
            with sqlite3.connect('./db/webtoons.db') as conn:
                cursor = conn.cursor()
                user = cursor.execute('SELECT * FROM users WHERE username = ?', (username,)).fetchone()

                if user and bcrypt.check_password_hash(user[2], password):
                    session['user_id'] = user[0]
                    user_obj = User(id=user[0], username=user[1], password=user[2])
                    login_user(user_obj)

                    bookmarks = get_bookmarks(user[0])
                    session['bookmarks'] = bookmarks

                    flash('Login successful!', 'success')
                    return redirect(url_for('index'))

        except Exception as e:
            print(f'Trouble logging in for {username}. Exception: {e}')
    
    return render_template('login.html', form=form)

@app.route('/logout')
def logout():
    logout_user()
    flash('Successfully logged out', 'info')
    return redirect(url_for('index'))

@app.route('/')
def index():
    # List the language options based on directory names from the 'data' folder
    languages = os.listdir(f'{path}')
    return render_template('index.html', languages=languages)

@app.route('/<language>')
def comics_list(language):
    # List available comics for the folder
    comics = os.listdir(f'{path}/{language}')
    return render_template('comics_list.html', language=language, comics=comics)

@app.route('/<language>/<comic>')
def episodes_list(language, comic):
    # List available episodes for the comic
    episodes = os.listdir(f'{path}/{language}/{comic}')
    episodes = sorted(episodes)
    upload_path = os.path.join(app.config['UPLOAD_FOLDER'], comic)
    if os.path.exists(upload_path):
        files = os.listdir(upload_path)
        if files:
            cover_filename = files[0]
    else:
        cover_filename = None
    return render_template('episodes_list.html', language=language, comic=comic, episodes=episodes, cover_filename=cover_filename)

@app.route('/<language>/<comic>/<episode>', methods=['GET', 'POST'])
def episode_page(language, comic, episode):
    user_id = session.get('user_id')
    bookmark_exists = False

    if user_id and 'bookmarks' in session:
        for bookmark in session['bookmarks']:
            if (bookmark['language'] == language and
                bookmark['comic_title'] == comic and
                bookmark['episode'] == episode):
                bookmark_exists = True
                break

    if request.method == 'POST':
        if user_id:
            if bookmark_exists:
                remove_bookmark(user_id, language, comic, episode)
                # Update cached bookmarks
                session['bookmarks'] = [b for b in session['bookmarks'] if not (b['language'] == language and b['comic_title'] == comic and b['episode'] == episode)]
                flash('Bookmark removed')
            else:
                add_bookmark(user_id, language, comic, episode)
                # Update cached bookmarks
                session['bookmarks'].append({'language': language, 'comic_title': comic, 'episode': episode})
                flash('Bookmark added')
        else:
            flash('Must be logged in to use bookmarks')

    # Get list of all available episodes
    episodes = os.listdir(f'{path}/{language}/{comic}')

    # Calculate prev and next episodes
    episode_num = int(episode)
    prev_ep_num = episode_num - 1
    prev_episode = str(prev_ep_num).zfill(3)
    next_ep_num = episode_num + 1
    next_episode = str(next_ep_num).zfill(3)

    # Handle episodes not existing
    if prev_episode not in episodes:
        prev_episode = episode
    if next_episode not in episodes:
        next_episode = episode

    # Images in the chapter folder
    images = os.listdir(f'{path}/{language}/{comic}/{episode}')
    images.sort()
    return render_template('episode.html', path=path, language=language, comic=comic, episode=episode, next_episode=next_episode, prev_episode=prev_episode, images=images, bookmark_exists=bookmark_exists)

@app.route('/images/<language>/<comic>/<episode>/<image>')
def serve_image(language, comic, episode, image):
    return send_from_directory(f'{path}/{language}/{comic}/{episode}', image)

@app.route('/add-comic', methods=['GET', 'POST'])
def add_comic():
    form = AddForm()
    if form.validate_on_submit():
        title = form.title.data
        url = form.url.data
        language = form.language.data
        cover_image = form.cover_image.data

        # Clean the title for directory path compatibility
        webtoon_title = title.lower()
        webtoon_title = webtoon_title.replace(" ", "_")

        cover_filename = None
        if cover_image:
            cover_filename = secure_filename(cover_image.filename)
            upload_path = os.path.join(app.config['UPLOAD_FOLDER'], webtoon_title)
            if not os.path.exists(upload_path):
                os.makedirs(upload_path)
            cover_image.save(os.path.join(upload_path, cover_filename))

        try:
            with sqlite3.connect('./db/webtoons.db') as conn:
                cursor = conn.cursor()
                cursor.execute('''
                    INSERT INTO comics (title, url, language, cover_image)
                    VALUES (?, ?, ?, ?)    
                ''', (webtoon_title, url, language, cover_filename))
                conn.commit()

            # Show success message
            flash(f'{title} Added Successfully!', 'success')

            # Redirect to clear the form
            return redirect(url_for('add_comic'))

        except Exception as e:
            print(f'Exception: {type(e).__name__} {e}')
            flash(f'An error occurred while trying to add {title}.', 'danger')

    return render_template('add_comic.html', form=form)

@app.route('/bookmarks')
@login_required
def bookmarks_view():
    user_id = session.get('user_id')
    if user_id:
        bookmarks = get_bookmarks(user_id)

    else:
        bookmarks = []

    return render_template('bookmarks.html', bookmarks=bookmarks)


if __name__=='__main__':
    init_db()  # Initialize database
    start_scheduler()  # Start scheduled tasks for webscraping
    app.run(debug=True)
