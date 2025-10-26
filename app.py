from flask import Flask, render_template, send_from_directory
import os


app = Flask(__name__)

@app.route('/')
def index():
    # List the comics based on directory names from the 'comics' folder
    comics = os.listdir('comics')
    return render_template('index.html', comics=comics)

@app.route('/comics/<comic>')
def comic_page(comic):
    # Chapters in the comic folder
    chapters = os.listdir(f'comics/{comic}')
    return render_template('comic.html')

@app.route('/comics/<comic>/<chapter>')
def chapter_page(comic, chapter):
    # Images in the chapter folder
    images = os.listdir(f'comics/{comic}/{chapter}')
    return render_template('chapter.html')
