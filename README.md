# Welcome to Zesje

Zesje is an online grading system for written exams.

## Development

### Setting up a development environment
Make sure you have `yarn` (installable via your local package manager), and Python 3.5 installed.

Install the necessary `yarn` dependencies:

    yarn install

We will keep the Python dependencies in a virtual environment:

    virtualenv venv
    source venv/bin/activate
    pip install -r requirements.txt
    
### Adding dependencies

#### Server-side
If you start using a new Python library, be sure to add it to `requirements.txt`

#### Client side
Yarn keeps track of all the client-side dependancies in `config.json` when you install new packages with `yarn add ...`
    
### Running a development server
run

    `yarn dev`

to start the development server, which you can access on http://127.0.0.1:8881.
It will automatically reload whenever you change any source files in `client/`
or `zesje/`.
