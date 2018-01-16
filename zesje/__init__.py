from os import path
from os.path import abspath, dirname
from flask import Flask

from . import db, api

app = Flask(__name__,
            static_folder=path.join(abspath(dirname(__file__)), 'static'))
db.use_db()

app.register_blueprint(api.app, url_prefix='/api')

@app.route('/')
@app.route('/<file>')
def index(file=None):
    return app.send_static_file(file or 'index.html')
