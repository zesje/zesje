# Welcome to Zesje

Zesje is an online grading system for written exams.

## Development

### Setting up a development environment

#### Install Conda
We highly recommend using [Conda](https://conda.io/docs/) when developing
Zesje, which will keep all the dependencies isolated. If you already
have the Anaconda Python distribution then you already have Conda installed,
otherwise follow the [installation instructions](https://conda.io/docs/user-guide/install/index.html)

#### Install the dependencies
To create a Conda environment and install the dependencies simply run
the following from the project root:

    conda env create  # this will use the 'environment.yml' in the project root
    conda activate zesje-dev
    yarn install  # install all the javascript dependencies

Make sure that you remember to `conda activate zesje-dev` when opening a new terminal window.

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
Adhere to [PEP8](https://www.python.org/dev/peps/pep-0008/), but use a column width of 120 characters (instead of 79).

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

#### Javascript
Adhere to [StandardJS](https://standardjs.com/).

If you use Visual Studio Code, install the [vscode-standardjs](https://marketplace.visualstudio.com/items?itemName=chenxsan.vscode-standardjs) plugin.

If you use Atom, install the [linter-js-standard-engine](https://atom.io/packages/linter-js-standard-engine) plugin.

### Adding dependencies

#### Server-side
If you start using a new Python library, be sure to add it to `environment.yml` and run
`conda env update` to install it.

#### Client-side
Yarn keeps track of all the client-side dependancies in `package.json` when you install new packages with `yarn add [packageName]`. Yarn will install and update your packages if your run

    yarn install

## License
Zesje is licensed under AGPLv3, which can be found in `LICENSE`. An summary of this license with it's permissions, conditions and limitations can be found [here](https://choosealicense.com/licenses/agpl-3.0/).
