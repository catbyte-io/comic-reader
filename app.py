from flask import Flask, render_template, request, url_for, send_from_directory, flash, redirect
from flask_wtf import FlaskForm
from wtforms import StringField, URLField, RadioField, FileField, SubmitField, PasswordField
from wtforms.validators import DataRequired, URL, EqualTo
from werkzeug.utils import secure_filename
from flask_wtf.file import FileAllowed
from tasks.scheduler import start_scheduler
from flask_bcrypt import Bcrypt

import os
import sqlite3


app = Flask(__name__, template_folder='./static/templates')
app.config['SECRET_KEY'] = '2ah!gh27#g40s5w5&-5f0ehjr@$&'  # For CSRF protection
app.config['UPLOAD_FOLDER'] = os.path.join('static', 'covers')
app.config['MAX_CONTENT_LENGTH'] = 16 * 1024 * 1024
bcrypt = Bcrypt(app)

# The path where comics are stored
path = '../../data'

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


def init_db():
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
                comic_title TEXT NOT NULL,
                episode TEXT NOT NULL,
                FOREIGN KEY(user_id) REFERENCES users(id) ON DELETE CASCADE
            )
        ''')
        conn.commit()


# Add an episode bookmark for a specific user
def add_bookmark(user_id, comic_title, episode):
    try:    
        with sqlite3.connect('./db/webtoons.db') as conn:
            cursor = conn.cursor()
            cursor.execute('INSERT INTO bookmarks (user_id, comic_title, episode) VALUES (?, ?, ?)', (user_id, comic_title, episode,))
            conn.commit()
    except Exception as e:
        print(f'Trouble adding bookmark. Exception: {e}')


# Remove an episode bookmark for a specific user
def remove_bookmark(user_id, comic_title, episode):
    try:    
        with sqlite3.connect('./db/webtoons.db') as conn:
            cursor = conn.cursor()
            cursor.execute('DELETE FROM bookmarks WHERE user_id = ? AND comic_title = ? AND episode = ?', (user_id, comic_title, episode,))
            conn.commit()
    except Exception as e:
        print(f'Trouble adding bookmark. Exception: {e}')


# Retrieve a user's bookmarks
def get_bookmarks(user_id):
    try:
        with sqlite3.connect('./db/webtoons.db') as conn:
            cursor = conn.cursor()
            cursor.execute('SELECT * FROM bookmarks WHERE user_id = ?', (user_id,))
            results = cursor.fetchall()
    except Exception as e:
        print(f'Trouble fetching bookmarks. Exception: {e}')


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
                    VALUES (?, ?,)    
                ''', (username, hashed_password,))
                conn.commit()

            # Show success message
            flash(f'{username} Added Successfully!', 'success')
        except Exception as e:
            print(f'Trouble adding {username}. Exception: {e}')

@app.route('/login', methods=['GET', 'POST'])
def login():
    form = LoginForm()
    if form.validate_on_submit():
        username = form.username.data
        password = form.password.data
        hashed_password = bcrypt.generate_password_hash(password).decode('utf-8')

        try:
            with sqlite3.connect('./db/webtoons.db') as conn:
                cursor = conn.cursor()
                user = cursor.execute('SELECT * FROM users WHERE username = ?', (username,)).fetchone()

                if user and bcrypt.check_password_hash(user[1], password):
                    flash('Login successful!', 'success')
                    return redirect(url_for('index'))

        except Exception as e:
            print(f'Trouble logging in for {username}. Exception: {e}')

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

@app.route('/<language>/<comic>/<episode>')
def episode_page(language, comic, episode):
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
    return render_template('episode.html', path=path, language=language, comic=comic, episode=episode, next_episode=next_episode, prev_episode=prev_episode, images=images)

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


if __name__=='__main__':
    init_db()  # Initialize database
    start_scheduler()  # Start scheduled tasks for webscraping
    app.run(debug=True)
