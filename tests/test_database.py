import pytest
from flask import Flask

from zesje.database import db, Exam, _generate_exam_token


@pytest.mark.parametrize('duplicate_count', [
    0, 1],
    ids=['No existing token', 'Existing token'])
def test_exam_generate_token_length_uppercase(duplicate_count, monkeypatch):
    class MockQuery:
        def __init__(self):
            self.duplicates = duplicate_count + 1

        def filter(self, *args):
                return self

        def first(self):
                self.duplicates -= 1
                return None if self.duplicates else True

    app = Flask(__name__, static_folder=None)
    app.config.update(
        SQLALCHEMY_DATABASE_URI='sqlite:///:memory:',
        SQLALCHEMY_TRACK_MODIFICATIONS=False  # Suppress future deprecation warning
    )
    db.init_app(app)

    with app.app_context():
        monkeypatch.setattr(Exam, 'query', MockQuery())

        id = _generate_exam_token()
        assert len(id) == 12
        assert id.isupper()
