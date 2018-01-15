from flask import Flask

app = Flask('zesje', static_folder='dist')

@app.route('/')
@app.route('/<file>')
def index(file=None):
    return app.send_static_file(file or 'index.html')
