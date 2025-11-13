from flask import Flask, render_template, request, url_for, send_from_directory
from flask_wtf import FlaskForm
from wtforms import StringField, URLField, RadioField, SubmitField
from wtforms.validators import DataRequired, URL

import os
import sqlite3


app = Flask(__name__, template_folder='./static/templates')
app.config["SECRET_KEY"] = '2ah!gh27#g40s5w5&-5f0ehjr@$&'  # For CSRF protection

# The path where comics are stored
path = '../../data'

# Define form
class AddForm(FlaskForm):
    title = StringField('title', validators=[DataRequired()])
    url = URLField('url', validators=[DataRequired(), URL()])
    language = RadioField('language', choices=[('english', 'English'), ('korean', 'Korean')], validators=[DataRequired()])
    submit = SubmitField('submit')

def init_db():
    with sqlite3.connect('./db/webtoons.db') as conn:
        cursor = conn.cursor()
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS comics (
                id INTEGER PRIMARY KEY,
                title TEXT NOT NULL,
                url TEXT NOT NULL,
                language TEXT NOT NULL,
                last_episode TEXT NOT NULL
            )
        ''')
        conn.commit()

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
    return render_template('episodes_list.html', language=language, comic=comic, episodes=episodes)

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
        last_episode = '0000'  # Default value

        try:
            with sqlite3.connect('./db/webtoons.db') as conn:
                cursor = conn.cursor()
                cursor.execute('''
                    INSERT INTO comics (title, url, language, last_episode)
                    VALUES (?, ?, ?)    
                ''', (title, url, language, last_episode))
                conn.commit()

        except Exception as e:
            print(f'Exception: {type(e).__name__} {e}')

    return render_template('add_comic.html', form=form)


if __name__=='__main__':
    init_db()
    app.run(debug=True)
