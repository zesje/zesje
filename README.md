# Welcome to Zesje

Zesje is an online grading system for written exams.

## Development

### Setting up a development environment
Make sure you have `npm`, `webpack` (installed via `npm`), and Python 3.5 installed.

Install the necessary `npm` dependencies:

    npm install

We will keep the Python dependencies in a virtual environment:

    virtualenv venv
    source venv/bin/activate
    pip install -r requirements.txt
    
### Adding dependencies

#### Server-side
If you start using a new Python library, be sure to add it to `requirements.txt`

#### Client side

    
### Running a development server
First build all the client-side assets:

    webpack --watch
    
the `--watch` flag tells webpack to rebuild the frontend code
whenever files in `client/` change.

Then, in a separate terminal, run the development server:
 
    python server

This will also re-load the code when you make modifications in `server/`.
