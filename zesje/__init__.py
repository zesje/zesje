""" Init file that starts a Flask dev server and opens db """
from celery import Celery

from ._version import __version__

__all__ = ["__version__", "celery"]


def make_celery(app_name=__name__):
    celery = Celery(app_name)

    return celery


celery = make_celery(app_name="zesje")
