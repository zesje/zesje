from os import path
from os.path import abspath, dirname, isfile
from flask import Flask
from flask_basicauth import BasicAuth

from . import db, api

static_folder_path = path.join(abspath(dirname(__file__)), 'static')

app = Flask(__name__,
            static_folder= static_folder_path)
db.use_db()


####### Very Very VERY import to use this outsite dev/sandbox environment
app.config['BASIC_AUTH_USERNAME'] = 'test'
app.config['BASIC_AUTH_PASSWORD'] = 'zesje'
app.config['BASIC_AUTH_FORCE'] = False # Don't forget to set this to 'True'
basic_auth = BasicAuth(app)


app.register_blueprint(api.app, url_prefix='/api')

@app.route('/')
@app.route('/<file>')
def index(file=''):
    if not isfile(path.join(static_folder_path, file)):
        file = 'index.html'
    return app.send_static_file(file)