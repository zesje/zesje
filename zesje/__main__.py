import os
import sys

sys.path.append(os.getcwd())
from zesje import factory  # noqa: E402
import zesje  # noqa: E402

app = factory.create_app(celery=zesje.celery)
app.run()
