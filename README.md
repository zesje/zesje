# Welcome to Zesje

Zesje is an online grading system for written exams.

## Development

### Setting up a development environment
Make sure you have Yarn and Python 3.6 installed.

Install the necessary Yarn dependencies:

    yarn install

We will keep the Python dependencies in a virtual environment:

    virtualenv venv
    source venv/bin/activate
    pip install -r requirements.txt -r requirements-dev.txt

Also install the required native dependencies:

| OS            | Command                      |
|---------------|------------------------------|
| macOS         | `brew install libdmtx`       |
| Debian/Ubuntu | `sudo apt install libdmtx0a` |
| Arch          | `pacman -S libdmtx`          |
| Fedora        | `dnf install libdmtx`        |
| openSUSE      | `zypper install libdmtx0`    |
| Windows       | *not necessary*              |

### Running a development server
Run

    yarn dev

to start the development server, which you can access on http://127.0.0.1:8881.
It will automatically reload whenever you change any source files in `client/`
or `zesje/`.

### Running the tests

You can run the tests by running

    yarn test

### Building and running the production version


### Code style

#### Python
Adhere to PEP8, but use a column width of 120 characters (instead of 79).

If you followed the instructions above, the linter `flake8` is installed in your virtual environment. If you use Visual Studio Code, install the [Python](https://marketplace.visualstudio.com/items?itemName=ms-python.python) extension and add the following lines to your workspace settings:

    "python.linting.pylintEnabled": false,
    "python.linting.flake8Enabled": true,
    "[python]": {
        "editor.rulers": [120]
    },

If you use Atom, install the [linter-flake8](https://atom.io/packages/linter-flake8) plugin and add the following lines to your config:

    ".source.python":
      "editor":
        "preferredLineLength": 120

### Adding dependencies

#### Server-side
If you start using a new Python library, be sure to add it to `requirements.txt`. Python libraries for the testing are in `requirements-dev.txt`.
The packages can be installed and updated in your environment by `pip` using

    pip install -r requirements.txt -r requirements-dev.txt


#### Client-side
Yarn keeps track of all the client-side dependancies in `package.json` when you install new packages with `yarn add [packageName]`. Yarn will install and update your packages if your run

    yarn install

## License
Zesje is licensed under AGPLv3, which can be found in `LICENSE`. An summary of this license with it's permissions, conditions and limitations can be found [here](https://choosealicense.com/licenses/agpl-3.0/).