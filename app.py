from flask import Flask, render_template, send_from_directory
import os


app = Flask(__name__)

@app.route('/')
def index():
    # List the language options based on directory names from the 'data' folder
    languages = os.listdir('data')
    return render_template('index.html', languages=languages)

@app.route('/<language>')
def comics_list(language):
    # List available comics for the folder
    comics = os.listdir(f'data/{language}')
    return render_template('comics_list.html', comics=comics)

@app.route('/<language>/<comic>')
def episodes_list(language, comic):
    # List available episodes for the comic
    episodes = os.listdir(f'data/{language}/{comic}')
    return render_template('episodes_list.html', episodes=episodes)

@app.route('/<language>/<comic>/<episode>')
def episode_page(comic, episode):
    # Images in the chapter folder
    images = os.listdir(f'data/{language}/{comic}/{episode}')
    return render_template('episode.html')
