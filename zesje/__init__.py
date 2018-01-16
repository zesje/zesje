from os import path
from os.path import abspath, dirname, isfile
from flask import Flask

from . import db, api

static_folder_path = path.join(abspath(dirname(__file__)), 'static')

app = Flask(__name__,
            static_folder= static_folder_path)
db.use_db()

app.register_blueprint(api.app, url_prefix='/api')

@app.route('/')
@app.route('/<file>')
def index(file=''):
    if not isfile(path.join(static_folder_path, file)):
        file = 'index.html'
    return app.send_static_file(file)