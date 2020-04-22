[![coverage report](https://gitlab.kwant-project.org/zesje/zesje/badges/master/coverage.svg)](https://gitlab.kwant-project.org/zesje/zesje/commits/master)

# Welcome to Zesje

Zesje is an online grading system for written exams.

## Running Zesje

### Running Zesje using Docker
Running Zesje using Docker is the easiest method to run Zesje
yourself with minimal technical knowledge required. For this approach
we assume that you already have [Docker](https://www.docker.com/)
installed, cloned the Zesje repository and entered its directory.

First create a volume to store the data:

    docker volume create zesje

Then build the Docker image using the following below. Anytime you
update Zesje by pulling the repository you have to run this command again.

    docker build -f auto.Dockerfile . -t zesje:auto

Finally, you can run the container to start Zesje using:

    docker run -p 8881:80 --volume zesje:/app/data-dev -it zesje:auto

Zesje should be available at http://127.0.0.1:8881. If you get
the error `502 - Bad Gateway` it means that Zesje is still starting.

## Development

### Setting up a development environment
*Zesje currently doesn't support native Windows, but WSL works.*

We recommend using the Conda tool for managing your development
environment. If you already have Anaconda or Miniconda installed,
you may skip this step.

Install Miniconda by following the instructions on this page:

https://conda.io/miniconda.html

Make sure you cloned this repository and enter its directory. Then
create a Conda environment that will automatically install all
of zesje's Python dependencies:

    conda env create  # Creates an environment from environment.yml

Then, *activate* the conda environment:

    conda activate zesje-dev

You should see `(zesje-dev)` inserted into your shell prompt.
This tells you that the environment is activated.

Install all of the Javascript dependencies:

    yarn install

Unfortunately there is also another dependency that must be installed
manually for now (we are working to bring this dependency into the
Conda ecosystem). You can install this dependency in the following way
on different platforms:

| OS                            | Command                       |
|-------------------------------|-------------------------------|
| macOS                         | `brew install libdmtx gcc`    |
| Debian <= 9, Ubuntu <= 19.04  | `apt install libdmtx0a gcc`   |
| Debian >= 10, Ubuntu >= 19.10 | `apt install libdmtx0b gcc`   |
| Arch                          | `pacman -S libdmtx gcc`       |
| Fedora                        | `dnf install libdmtx gcc`     |
| openSUSE                      | `zypper install libdmtx0 gcc` |


#### Setting up MySQL server

If this is the first time that you will run Zesje with MySQL in
development, then first run the following command from the Zesje
repository directory:

    yarn mysql-create

That's all it needs to create the MySQL files in the data directory.
Although the database is now empty, it will automatically be populated
with the previous `sqlite3` data once the app starts.

In case you want to start MySQL without running the app use

    yarn dev:mysql-start

and, immeditaly after, migrate the database to create the tables and fill it
with previous data running

    yarn dev:migrate

That's all, MySQL is now fully functional but remember to stop it
once you quit the development process with

    yarn mysql-stop


### Running a development server
Activate your zesje development environment and run

    yarn dev

to start the development server, which you can access on http://127.0.0.1:8881.
It will automatically reload whenever you change any source files in `client/`
or `zesje/`.

### Generate sample data

The script `example_data.py` can be used to create a sample exam that mimics the appearance and behavior of a typical grading process in Zesje. The prototype exam consist on 3 open answer questions per page and 1 multiple choice question per page (excluding the first one). The script partially solves those questions and assigns random feedback to the answered questions while the not answered questions are processed as blank.

The script is called from the command line with the following parameters:
 - `-d, --delete`  If specified, removes any existing data and creates a new empty database. Otherwise, new exams are added without deleting previous data.
 - `--exams (int)` the number of exams to add, default is 1.
 - `--pages (int)` the number of pages per exam, default is 3.
 - `--students (int)` the number of students per exam, default is 30
 - `--graders (int)` the number of graders to add, default is 4.
 - `--solve (float)` between 0 and 1, indicates the percentage of questions to answer (including MCQ), default is 90%.
 - `--grade (float)` between 0 and 1, indicate the percentage of solved questions to grade (that is, excluding blank answers), default is 60%.

The actual processing of the exam takes a while, specially when the number of students is large.

### Running the tests

You can run the tests by running

    yarn test

#### Viewing test coverage

As a test coverage tool for Python tests, `pytest-cov` is used.

To view test coverage, run

    yarn test:py:cov

A coverage report is now generated in the terminal, as an XML file, and in HTML format.
The HTML file shows an overview of untested code in red.

##### Viewing coverage in Visual Studio Code

There is a plugin called Coverage Gutter that will highlight which lines of code are covered.
Simply install Coverage Gutter, after which a watch button appears in the colored box at the bottom of your IDE.
When you click watch, green and red lines appear next to the line numbers indicating if the code is covered.

Coverage Gutter uses the XML which is produced by `yarn test:py:cov`, called `cov.xml`. This file should be located in the main folder.

##### Viewing coverage in PyCharm
To view test coverage in PyCharm, run `yarn test:py:cov` to generate the coverage report XML file `cov.xml` if it is not present already.

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

    yarn dev:migrate # (for the development database)
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
If you start using a new Python library, be sure to add it to `environment.yml`.
The packages can be installed and updated in your environment by `conda` using

    conda env update

#### Client-side
Yarn keeps track of all the client-side dependancies in `package.json` when you install new packages with `yarn add [packageName]`. Yarn will install and update your packages if your run

    yarn install

## License
Zesje is licensed under AGPLv3, which can be found in `LICENSE`. An summary of this license with it's permissions, conditions and limitations can be found [here](https://choosealicense.com/licenses/agpl-3.0/).
