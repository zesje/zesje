from hashlib import md5
from webargs.flaskparser import FlaskParser
from webargs import ValidationError, fields, validate


def non_empty_string(text):
    if not text.strip():
        raise ValidationError("String must not be empty")


class ZesjeParser(FlaskParser):

    DEFAULT_VALIDATION_STATUS = 404
    DEFAULT_LOCATION = 'view_args'


parser = ZesjeParser()
use_args = parser.use_args
use_kwargs = parser.use_kwargs


# @parser.error_handler
# def handle_request_parsing_error(err, req, schema, *, error_status_code, error_headers):
#     """webargs error handler that uses Flask-RESTful's abort function to return
#     a JSON error response to the client.
#     """
#     print(err, req, schema, error_status_code, error_headers)
#     abort(error_status_code, errors=err.messages)


class DBModel(fields.Integer):
    """Marshmallow field that converts integer identifier into database objects.

    Attributes
    ----------
    model: db.Model
        the database model to initiate.
    validate_model: list of `Validator`
        the validators to use when the model has been loaded

    Exceptions
    ----------
    ValidationError
        * `id` is not a valid integer
        * `id` is smaller than 1
        * Model with `id` does not exist in database
        * Model does not satisfy the `validate_model` requirements
    """

    default_error_messages = {
        "not_in_range": "Id must be larger than 1.",
        'not_found': "{model} with id #{id} does not exist."
    }

    def __init__(self, model, validate_model=None, **kwargs):
        super().__init__(**kwargs)
        self.model = model
        self.validate_model = validate_model

    def _validated(self, value):
        """Format the value or raise a :exc:`ValidationError` if an error occurs."""
        id = super()._validated(value)
        if id < 1:  # MySQL db identifiers start at 1
            raise self.make_error('not_in_range')

        return id

    def _validate_all_model(self, item):
        if not self.validate_model:
            return True

        validate.And(*self.validate_model)(item)

    def _serialize(self, value, attr, obj, **kwargs):
        """Converts a `db.Model` into a python integer identifying the item."""
        if value is None:
            return None

        return str(value.id)

    def _deserialize(self, value, attr, data, **kwargs):
        """COnverts the MySQL identifier into the corresponding `db.Model`."""
        id = super()._deserialize(value, attr, data, **kwargs)
        if id is None:
            return None

        item = self.model.query.get(id)
        if item is None:
            raise self.make_error("not_found", id=value, model=self.model.__name__)

        self._validate_all_model(item)
        return item


def _shuffle(to_shuffle, shuffle_seed, key_extractor=lambda v: v):
    """
    Uniquely sorts a list based on some seed.

    Parameters
    ----------
    to_shuffle : iterable
        the list to shuffle.
    shuffle_seed : int
        the seed to shuffle this list with.
    key_extractor : lambda
        function to extract the key to sort on from the objects in to_shuffle.

    Returns
    -------
    a copy of to_shuffle, sorted uniquely based on it's own key and shuffle_seed.
    """
    return sorted(to_shuffle, key=lambda s: md5(f'{key_extractor(s)}, {shuffle_seed}'.encode('utf-8')).digest())
