""" Init file that starts a Flask dev server and opens db """

import os
from os.path import abspath, dirname

from flask import Flask
from flask_basicauth import BasicAuth
from werkzeug.exceptions import NotFound

from .api import api_bp
from .database import db
from ._version import __version__


__all__ = ['__version__', 'app']

STATIC_FOLDER_PATH = os.path.join(abspath(dirname(__file__)), 'static')

app = Flask(__name__, static_folder=STATIC_FOLDER_PATH)
app.register_blueprint(api_bp, url_prefix='/api')
auth = BasicAuth()  # don't pass 'app', as its not yet configured

if 'ZESJE_SETTINGS' in os.environ:
    app.config.from_envvar('ZESJE_SETTINGS')

# Default settings
app.config.update(
    DATA_DIRECTORY=abspath(app.config.get('DATA_DIRECTORY', 'data')),
)

# These reference DATA_DIRECTORY, so they need to be in a separate update
app.config.update(
    SCAN_DIRECTORY=os.path.join(app.config['DATA_DIRECTORY'], 'scans'),
    DB_PATH=os.path.join(app.config['DATA_DIRECTORY'], 'course.sqlite'),
)


@app.before_first_request
def setup():
    auth.init_app(app)

    os.makedirs(app.config['DATA_DIRECTORY'], exist_ok=True)
    os.makedirs(app.config['SCAN_DIRECTORY'], exist_ok=True)

    db.bind('sqlite', app.config['DB_PATH'], create_db=True)
    db.generate_mapping(create_tables=True)


@app.route('/')
@app.route('/<path:path>')
def index(path='index.html'):
    """Serve the static react content, otherwise fallback to the index.html

    React Router will decide what to do with the URL in that case.
    """
    try:
        return app.send_static_file(path)
    except NotFound:
        return app.send_static_file('index.html')
