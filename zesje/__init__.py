""" Init file that starts a Flask dev server and opens db """

import os
from os.path import abspath, dirname

from flask import Flask
from werkzeug.exceptions import NotFound
from flask_basicauth import BasicAuth

from .api import api_bp
from .models import db


STATIC_FOLDER_PATH = os.path.join(abspath(dirname(__file__)), 'static')

app = Flask(__name__, static_folder=STATIC_FOLDER_PATH)
app.register_blueprint(api_bp, url_prefix='/api')
auth = BasicAuth()  # don't pass 'app', as its not yet configured

# Default settings
app.config.update(
    DATA_DIRECTORY=os.path.join(os.getcwd(), 'data')
)
if 'ZESJE_SETTINGS' in os.environ:
    app.config.from_envvar('ZESJE_SETTINGS')


@app.before_first_request
def setup():
    auth.init_app(app)

    data_dir = app.config['DATA_DIRECTORY']
    os.makedirs(data_dir, exist_ok=True)
    os.makedirs(os.path.join(data_dir, 'pdfs'), exist_ok=True)

    db.bind('sqlite', f"{app.config['DATA_DIRECTORY']}/course.sqlite", create_db=True)
    db.generate_mapping(create_tables=True)


@app.route('/')
@app.route('/<file>')
def index(file='index.html'):
    """Serve the static react content, otherwise fallback to the index.html"""
    try:
        return app.send_static_file(file)
    except NotFound:
        return app.send_static_file('index.html')
