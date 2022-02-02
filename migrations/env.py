from __future__ import with_statement

import logging
import sys
import os

from alembic import context
from sqlalchemy import engine_from_config, pool
from logging.config import fileConfig
from datetime import datetime
from shutil import copy


from flask import current_app

sys.path.append(os.getcwd())
from zesje.database import db  # noqa: E402
from zesje.mysql import dump  # noqa: E402


config = context.config
fileConfig(config.config_file_name)
logger = logging.getLogger('alembic.env')

config.set_main_option('sqlalchemy.url',
                       current_app.config.get('SQLALCHEMY_DATABASE_URI'))

target_metadata = db.metadata


def run_migrations_offline():
    """Run migrations in 'offline' mode.

    This configures the context with just a URL
    and not an Engine, though an Engine is acceptable
    here as well.  By skipping the Engine creation
    we don't even need a DBAPI to be available.

    Calls to context.execute() here emit the given string to the
    script output.

    """
    url = config.get_main_option("sqlalchemy.url")
    context.configure(url=url)

    with context.begin_transaction():
        context.run_migrations()


def run_migrations_online():
    """Run migrations in 'online' mode.

    In this scenario we need to create an Engine
    and associate a connection with the context.

    """

    # this callback is used to prevent an auto-migration from being generated
    # when there are no changes to the schema
    # reference: http://alembic.zzzcomputing.com/en/latest/cookbook.html
    def process_revision_directives(context, revision, directives):
        if getattr(config.cmd_opts, 'autogenerate', False):
            script = directives[0]
            if script.upgrade_ops.is_empty():
                directives[:] = []
                logger.info('No changes in schema detected.')

    engine = engine_from_config(config.get_section(config.config_ini_section),
                                prefix='sqlalchemy.',
                                poolclass=pool.NullPool)

    # Create database directory if it does not exist yet
    db_url = config.get_main_option("sqlalchemy.url")
    is_sqlite = db_url.startswith('sqlite:///')
    if is_sqlite:
        db_path = db_url.replace('sqlite:///', '')
        db_dir = os.path.dirname(db_path)
        os.makedirs(db_dir, exist_ok=True)

    connection = engine.connect()

    # Only pass metadata when generating migrations, not when running them.
    # This prevents unintended side effects of metadata changes in newer commits.
    metadata_arg = dict(target_metadata=target_metadata) if getattr(config.cmd_opts, 'autogenerate', False) else {}

    context.configure(connection=connection,
                      process_revision_directives=process_revision_directives,
                      render_as_batch=True,
                      **metadata_arg,
                      **current_app.extensions['migrate'].configure_args)

    to_revision = context.get_head_revision()
    from_revision = context.get_context().get_current_revision()

    # Create database backup if a migration is pending
    if is_sqlite and os.path.isfile(db_path):
        db_file = os.path.basename(db_path)
        timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
        db_backup_file = 'backup_{}_{}'.format(timestamp, db_file)
        db_backup_path = os.path.join(db_dir, db_backup_file)
        if not os.path.isfile(db_backup_path) and from_revision != to_revision:
            copy(db_path, db_backup_path)
    elif db_url.startswith('mysql://'):
        timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
        db_backup_path = os.path.join(
            current_app.config['DATA_DIRECTORY'],
            'backup_{}_{}.sql'.format(timestamp, current_app.config['MYSQL_DATABASE'])
        )
        try:
            output = dump(current_app.config, current_app.config['MYSQL_DATABASE'])
            with open(db_backup_path, 'wb') as outf:
                outf.write(output)
        except Exception as e:
            print('Could not backup database: ' + str(e))

    try:
        with context.begin_transaction():
            context.run_migrations()
    except Exception as exception:
        logger.error(exception)
        raise exception
    finally:
        connection.close()


if context.is_offline_mode():
    run_migrations_offline()
else:
    run_migrations_online()
