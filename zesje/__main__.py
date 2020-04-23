import os
import sys

sys.path.append(os.getcwd())
from zesje import factory  # noqa: E402
from zesje import mysql  # noqa: E402
import zesje  # noqa: E402

app = factory.create_app(celery=zesje.celery)

if mysql.create(app):
    mysql.start(app)
else:
    raise ValueError('Could not create mysql.')

app.run()

mysql.stop(app)
