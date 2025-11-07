from flask import Flask, render_template, request, url_for, send_from_directory

import os
import sqlite3


app = Flask(__name__, template_folder='./static/templates')

path = '../../data'

def init_db():
    with sqlite3.connect('./db/webtoons.db') as conn:
        cursor = conn.cursor()
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS entries (
                id INTEGER PRIMARY KEY,
                title TEXT NOT NULL,
                url TEXT NOT NULL,
                language TEXT NOT NULL
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
    # Images in the chapter folder
    images = os.listdir(f'{path}/{language}/{comic}/{episode}')
    return render_template('episode.html', language=language, comic=comic, episode=episode, images=images)

@app.route('/add-comic', methods=['GET', 'POST'])
def add_comic():
    if request.method == 'POST':
        title = request.form['title']
        url = request.form['url']
        language = request.form['language']



if __name__=='__main__':
    init_db()
    app.run(debug=True)
