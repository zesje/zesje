import sys
import os
from os.path import dirname
from argparse import ArgumentParser

import jinja2


INIT_FILE_TEMPLATE = """CREATE DATABASE IF NOT EXISTS course;
CREATE DATABASE IF NOT EXISTS course_test;

CREATE USER IF NOT EXISTS '{{MYSQL_USER}}'@'%' IDENTIFIED BY '{{MYSQL_PSW}}';
GRANT ALL ON course.* TO '{{MYSQL_USER}}'@'%';
GRANT ALL ON course_test.* TO '{{MYSQL_USER}}'@'%';

ALTER USER 'root'@'localhost' IDENTIFIED BY '{{MYSQL_ROOT_PSW}}';

FLUSH PRIVILEGES;
"""


def create(config):
    os.makedirs(config['DATA_DIRECTORY'], exist_ok=True)

    datadir = config['MYSQL_DIRECTORY']
    if not os.path.exists(datadir):
        initfile = os.path.join(dirname(config['DATA_DIRECTORY']), 'myinit.sql')

        _create_init_file(initfile, config)

        code = os.system(f'mysqld {_default_options(datadir)} --init-file={initfile} --initialize;')

        os.remove(initfile)

        if code != 0:
            raise ValueError('Error creating MySQL, please see log files for details.')


def start(config, interactive=False):
    datadir = config['MYSQL_DIRECTORY']
    code = os.system(
        f'mysqld_safe {_default_options(datadir)} --mysqld=$CONDA_PREFIX/bin/mysqld --gdb'
        + ('' if interactive else ' &')
    )

    if code != 0:
        raise ValueError('Error starting MySQL, please see log files for details.')


def stop(config):
    psw = config['MYSQL_ROOT_PSW']
    os.system(f'mysqladmin --user=root --password={psw} shutdown')


def _create_init_file(filepath, config):
    template = jinja2.Template(INIT_FILE_TEMPLATE)
    rendered = template.render(config)

    with open(filepath, 'w') as out_file:
        out_file.write(rendered)


def _default_options(datadir):
    return f'--basedir=$CONDA_PREFIX/bin --datadir={datadir} --lc-messages-dir=$CONDA_PREFIX/share/mysql'


def main(action, interactive):
    config = Config(dirname(dirname(__file__)))
    create_config(config, None)

    if action == 'create':
        create(config)
    elif action == 'start':
        start(config, interactive)
    elif action == 'stop':
        stop(config)


if __name__ == '__main__':
    from flask import Config
    from .factory import create_config

    parser = ArgumentParser(description='Control MySQL database')
    parser.add_argument('action', choices=['create', 'start', 'stop'], help='Action to be performed')
    parser.add_argument('-i',
                        action='store_true',
                        help='Run commant in interactive mode, attached to the console.')

    args = parser.parse_args(sys.argv[1:])
    main(args.action, args.i)
