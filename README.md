[![coverage report](https://gitlab.kwant-project.org/works-on-my-machine/zesje/badges/master/coverage.svg)](https://gitlab.kwant-project.org/works-on-my-machine/zesje/commits/pytest-cov)

# Welcome to Zesje

Zesje is an online grading system for written exams.

## Development

### Setting up a development environment
We recommend using the Conda tool for managing your development
environment. If you already have Anaconda or Miniconda installed,
you may skip this step.

Install Miniconda by following the instructions on this page:

https://conda.io/miniconda.html

Create a Conda environment that you will use for installing all
of zesje's dependencies:

    conda create -c conda-forge -n zesje-dev python=3.6 yarn

Then, *activate* the conda environment:

    conda activate zesje-dev

You should see `(zesje-dev)` inserted into your shell prompt.
This tells you that the environment is activated.

Install all of the Javascript dependencies:

    yarn install

Install all of the Python dependencies:

    pip install -r requirements.txt -r requirements-dev.txt

Unfortunately there is also another dependency that must be installed
manually for now (we are working to bring this dependency into the
Conda ecosystem). You can install this dependency in the following way
on different platforms:

| OS            | Command                      |
|---------------|------------------------------|
| macOS         | `brew install libdmtx`       |
| Debian/Ubuntu | `sudo apt install libdmtx0a` |
| Arch          | `pacman -S libdmtx`          |
| Fedora        | `dnf install libdmtx`        |
| openSUSE      | `zypper install libdmtx0`    |
| Windows       | *not necessary*              |



### Running a development server
Activate your zesje development environment and run

    yarn dev

to start the development server, which you can access on http://127.0.0.1:8881.
It will automatically reload whenever you change any source files in `client/`
or `zesje/`.

### Running the tests

You can run the tests by running

    yarn test
    
#### Viewing test coverage

As a test coverage tool, `pytest-cov` is used.

To view test coverage, run

    yarn cov

Or use Conda in the Zesje repo and run `python -m pytest --cov=zesje tests/`

##### Viewing coverage in Visual Studio Code

There is a plugin called Coverage Gutter that will highlight which lines of code are covered.
Simply install Coverage Gutter, after which a watch button appears in the colored box at the bottom of your IDE.
When you click watch, green and red lines appear next to the line numbers indicating if the code is covered.

Coverage Gutter uses the XML which is produced by `yarn cov`, called `cov.xml`. This file should be located in the main folder.

##### Viewing coverage in PyCharm
To view test coverage in PyCharm, run `yarn cov` to generate the coverage report XML file `cov.xml` if it is not present already.

Next, open up PyCharm and in the top bar go to **Run -> Show Code Coverage Data** (Ctrl + Alt + F6).

Press **+** and add the file `cov.xml` that is in the main project directory.
A code coverage report should now appear in the side bar on the right.

#### Policy errors

If you encounter PolicyErrors related to ImageMagick in any of the previous steps, please
try the instructions listed
[here](https://alexvanderbist.com/posts/2018/fixing-imagick-error-unauthorized) as
a first resort.

### Database modifications

Zesje uses Flask-Migrate and Alembic for database versioning and migration. Flask-Migrate is an extension that handles SQLAlchemy database migrations for Flask applications using Alembic. 

To change something in the database schema, simply add this change to `zesje/database.py`. After that run the following command to prepare a new migration:

    yarn prepare-migration

This uses Flask-Migrate to make a new migration script in `migrations/versions` which needs to be reviewed and edited. Please suffix the name of this file with something distinctive and add a short description at the top of the file. To apply the database migration run:

    yarn migrate:dev # (for the development database)
    yarn migrate # (for the production database)

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
If you start using a new Python library, be sure to add it to `requirements.txt`. Python libraries for the testing are in `requirements-dev.txt`.
The packages can be installed and updated in your environment by `pip` using

    pip install -r requirements.txt -r requirements-dev.txt


#### Client-side
Yarn keeps track of all the client-side dependancies in `package.json` when you install new packages with `yarn add [packageName]`. Yarn will install and update your packages if your run

    yarn install

## License
Zesje is licensed under AGPLv3, which can be found in `LICENSE`. An summary of this license with it's permissions, conditions and limitations can be found [here](https://choosealicense.com/licenses/agpl-3.0/).
