""" Init file that starts a Flask dev server and opens db """

from os import path
from os.path import abspath, dirname

from flask import Flask
from flask_basicauth import BasicAuth
from werkzeug.exceptions import NotFound

from api import api_bp
from models import db


STATIC_FOLDER_PATH = path.join(abspath(dirname(__file__)), 'static')

app = Flask(__name__, static_folder=STATIC_FOLDER_PATH)
app.register_blueprint(api_bp, url_prefix='/api')


####### Very Very VERY import to use this outsite dev/sandbox environment
app.config['BASIC_AUTH_USERNAME'] = 'test'
app.config['BASIC_AUTH_PASSWORD'] = 'zesje'
app.config['BASIC_AUTH_FORCE'] = False # Don't forget to set this to 'True'
basic_auth = BasicAuth(app)

db.bind('sqlite', 'course.sqlite')
db.generate_mapping(create_tables=True)

@app.route('/')
@app.route('/<file>')
def index(file='index.html'):
    """Serve the static react content, otherwise fallback to the index.html"""
    try:
        return app.send_static_file(file)
    except NotFound:
        return app.send_static_file('index.html')
