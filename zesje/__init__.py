""" Init file that starts a Flask dev server and opens db """

import os

from werkzeug.exceptions import NotFound

from .factory import create_app, make_celery
from .api import api_bp

from ._version import __version__


__all__ = ['__version__', 'app']

app = create_app()

app.register_blueprint(api_bp, url_prefix='/api')

os.makedirs(app.config['DATA_DIRECTORY'], exist_ok=True)
os.makedirs(app.config['SCAN_DIRECTORY'], exist_ok=True)

celery = make_celery(app)


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
