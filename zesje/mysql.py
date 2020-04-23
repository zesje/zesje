import os
from os.path import dirname

import jinja2


INIT_FILE_TEMPLATE = """CREATE DATABASE IF NOT EXISTS course;
CREATE DATABASE IF NOT EXISTS course_test;

CREATE USER IF NOT EXISTS '{{MYSQL_USER}}'@'%' IDENTIFIED BY '{{MYSQL_PSW}}';
GRANT ALL ON course.* TO '{{MYSQL_USER}}'@'%';
GRANT ALL ON course_test.* TO '{{MYSQL_USER}}'@'%';

ALTER USER 'root'@'localhost' IDENTIFIED BY '{{MYSQL_ROOT_PSW}}';

FLUSH PRIVILEGES;
"""


def create(app):
    os.makedirs(app.config['DATA_DIRECTORY'], exist_ok=True)

    datadir = app.config['MYSQL_DIRECTORY']
    if not os.path.exists(datadir):
        initfile = os.path.join(dirname(app.config['DATA_DIRECTORY']), 'myinit.sql')

        _create_init_file(initfile, app.config)

        code = os.system(f'mysqld --basedir=$CONDA_PREFIX/bin --datadir={datadir}'
                         f'--lc-messages-dir=$CONDA_PREFIX/share/mysql --init-file={initfile} --initialize;')

        os.remove(initfile)

        return code == 0

    return True


def start(app):
    datadir = app.config['MYSQL_DIRECTORY']
    return os.system(f'mysqld_safe --basedir=$CONDA_PREFIX/bin/ --datadir={datadir} '
                     '--mysqld=$CONDA_PREFIX/bin/mysqld --gdb &')


def stop(app):
    psw = app.config['MYSQL_ROOT_PSW']
    os.system(f'mysqladmin --user=root --password={psw} shutdown')


def _create_init_file(filepath, config):
    template = jinja2.Template(INIT_FILE_TEMPLATE)
    rendered = template.render(config)

    with open(filepath, 'w') as out_file:
        out_file.write(rendered)
