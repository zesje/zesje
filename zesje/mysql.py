import sys
import os
import errno
import configparser
import time
import subprocess as sp


from pathlib import Path
from os.path import dirname
from argparse import ArgumentParser

import jinja2


INIT_FILE_TEMPLATE = """CREATE DATABASE IF NOT EXISTS course;
CREATE DATABASE IF NOT EXISTS course_test;

CREATE USER IF NOT EXISTS '{{MYSQL_USER}}'@'%' IDENTIFIED BY '{{MYSQL_PASSWORD}}';
GRANT ALL ON course.* TO '{{MYSQL_USER}}'@'%';
GRANT ALL ON course_test.* TO '{{MYSQL_USER}}'@'%';

ALTER USER 'root'@'localhost' IDENTIFIED BY '{{MYSQL_ROOT_PASSWORD}}';

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
        return True
    else:
        print('MySQL is already initialized.')
        if not allow_exists:
            _exit(1)
        return False


def start(config, interactive=False, allow_running=False):
    datadir = config['MYSQL_DIRECTORY']
    if not Path(datadir).exists():
        print(f'MySQL is not yet initialized at {datadir}')
        _exit(1)
        return False

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
    password = config['MYSQL_ROOT_PASSWORD']
    host = config['MYSQL_HOST']
    os.system(f'mysqladmin --host={host} --user=root --password={password} shutdown')


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


def dump(config, database=None):
    user = config['MYSQL_USER']
    password = config['MYSQL_PASSWORD']
    host = config['MYSQL_HOST']
    database = database if database is not None else config['MYSQL_DATABASE']
    p = sp.Popen(
        ['mysqldump', f'--user={user}', f'--password={password}', f'--host={host}', database],
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


# From https://stackoverflow.com/a/6940314
def pid_exists(pid):
    """Check whether pid exists in the current process table.
    UNIX only.
    """
    if pid < 0:
        return False
    if pid == 0:
        # According to "man 2 kill" PID 0 refers to every process
        # in the process group of the calling process.
        # On certain systems 0 is a valid PID but we have no way
        # to know that in a portable fashion.
        raise ValueError('invalid PID 0')
    try:
        os.kill(pid, 0)
    except OSError as err:
        if err.errno == errno.ESRCH:
            # ESRCH == No such process
            return False
        elif err.errno == errno.EPERM:
            # EPERM clearly means there's a process to deny access to
            return True
        else:
            # According to "man 2 kill" possible error values are
            # (EINVAL, EPERM, ESRCH)
            raise
    else:
        return True


def _pid_file(datadir):
    pid_file = Path(datadir) / _defaults_file_option('pid_file')
    return pid_file if (pid_file.exists() and pid_exists(int(pid_file.read_text()))) else None


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
