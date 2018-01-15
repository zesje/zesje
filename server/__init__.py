from flask import Flask

from . import db, api

app = Flask('zesje', static_folder='dist')
db.use_db()

app.register_blueprint(api.app, url_prefix='/api')

@app.route('/')
@app.route('/<file>')
def index(file=None):
    return app.send_static_file(file or 'index.html')
