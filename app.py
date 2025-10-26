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
    # Images in the comic folder
    images = os.listdir(f'comics/{comic}')
    return render_template('comic.html')
