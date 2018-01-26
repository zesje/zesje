from os import path
from os.path import abspath, dirname

from flask import Flask
from flask_basicauth import BasicAuth
from werkzeug.exceptions import NotFound

from . import db, api

STATIC_FOLDER_PATH = path.join(abspath(dirname(__file__)), 'static')

app = Flask(__name__, static_folder=STATIC_FOLDER_PATH)
app.register_blueprint(api.api_bp, url_prefix='/api')


####### Very Very VERY import to use this outsite dev/sandbox environment
app.config['BASIC_AUTH_USERNAME'] = 'test'
app.config['BASIC_AUTH_PASSWORD'] = 'zesje'
app.config['BASIC_AUTH_FORCE'] = False # Don't forget to set this to 'True'
basic_auth = BasicAuth(app)


db.use_db()

@app.route('/')
@app.route('/<file>')
def index(file='index.html'):
    """Serve the static react content, otherwise fallback to the index.html"""
    try:
        return app.send_static_file(file)
    except NotFound:
        return app.send_static_file('index.html')
