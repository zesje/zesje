import sys
import os
import configparser
import time
import psutil
import subprocess as sp


from pathlib import Path
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


def create(config, allow_exists):
    os.makedirs(config['DATA_DIRECTORY'], exist_ok=True)

    datadir = config['MYSQL_DIRECTORY']
    if not os.path.exists(datadir):
        print('Initializing MySQL...')
        initfile = os.path.join(dirname(config['DATA_DIRECTORY']), 'myinit.sql')

        _create_init_file(initfile, config)

        command = f'mysqld {_default_options(datadir)} --init-file={initfile} --initialize'
        print(command)
        status_code = os.system(command)

        os.remove(initfile)

        if status_code != 0:
            raise ValueError('Error creating MySQL, please see log files for details.')
    else:
        print('MySQL is already initialized.')
        if not allow_exists:
            _exit(1)


def start(config, interactive=False, allow_running=False):
    datadir = config['MYSQL_DIRECTORY']
    pid_file = _pid_file(datadir)
    if pid_file:
        print(f'MySQL is running, PID file for MySQL already exists at {pid_file}')
        if allow_running:
            if not interactive:
                print('Will not start MySQL, continuing...')
                _exit(0)
                return True
            else:
                print('Will not start MySQL, waiting for interrupt...')
                sys.stdout.flush()
                try:
                    while True:
                        time.sleep(1)
                except KeyboardInterrupt:
                    _exit(0)
        else:
            print('Will not start MySQL, exiting...')
            _exit(1)
            return False
    else:
        command = f'mysqld {_default_options(datadir)} --gdb'
        print(command)

        if interactive:
            code = os.system(command)

            try:
                time.sleep(1.0)
            except KeyboardInterrupt:
                print('Stopping MySQL...')
        else:
            command += ' &'
            code = os.system(command)

            if code != 0:
                raise ValueError('Error starting MySQL, please see log files for details.')


def stop(config):
    psw = config['MYSQL_ROOT_PSW']
    host = config['MYSQL_HOST']
    os.system(f'mysqladmin --host={host} --user=root --password={psw} shutdown')


def is_running(config):
    datadir = config['MYSQL_DIRECTORY']
    pid_file = _pid_file(datadir)
    if pid_file:
        print(f'MySQL is running, PID file exists at {pid_file}')
        _exit(0)
        return True
    else:
        print(f'MySQL is not running')
        _exit(1)
        return False


def dump(config, database):
    psw = config['MYSQL_ROOT_PSW']
    host = config['MYSQL_HOST']
    p = sp.Popen(
        ['mysqldump', '-uroot', f'--password={psw}', f'--host={host}', database],
        stdin=sp.PIPE,
        stdout=sp.PIPE,
        stderr=sp.PIPE
    )
    output, err = p.communicate()

    if p.returncode != 0:
        raise ValueError(f'mysqldump exited with error code {p.returncode}')

    return output


def _exit(code):
    if __name__ == '__main__':
        exit(code)


def _pid_file(datadir):
    pid_file = Path(datadir) / _defaults_file_option('pid_file')
    return pid_file if (pid_file.exists() and psutil.pid_exists(int(pid_file.read_text()))) else None


def _create_init_file(filepath, config):
    template = jinja2.Template(INIT_FILE_TEMPLATE)
    rendered = template.render(config)

    with open(filepath, 'w') as out_file:
        out_file.write(rendered)


def _defaults_file():
    return Path.cwd() / 'mysql.conf'


def _defaults_file_option(option):
    config = configparser.ConfigParser()
    config.read(_defaults_file())
    return config['mysqld'][option]


def _default_options(datadir):
    return f'--defaults-file={_defaults_file()} --datadir={datadir} --basedir=$CONDA_PREFIX/bin ' + \
        '--lc-messages-dir=$CONDA_PREFIX/share/mysql'


def main(action, args):
    config = Config(dirname(dirname(__file__)))
    create_config(config, None)

    if action == 'create':
        create(config, args.allow_exists)
    elif action == 'start':
        start(config, args.i, args.allow_running)
    elif action == 'stop':
        stop(config)
    elif action == 'is-running':
        is_running(config)


if __name__ == '__main__':
    from flask import Config
    from .factory import create_config

    parser = ArgumentParser(description='Control MySQL database')
    parser.add_argument('action', choices=['create', 'start', 'stop', 'is-running'], help='Action to be performed')
    parser.add_argument('-i',
                        action='store_true',
                        help='Run commant in interactive mode, attached to the console.')
    parser.add_argument('--allow-running',
                        action='store_true',
                        help='Allow the MySQL server to be already running.')
    parser.add_argument('--allow-exists',
                        action='store_true',
                        help='Allow MySQL to be initialized already.')

    args = parser.parse_args(sys.argv[1:])
    main(args.action, args)
