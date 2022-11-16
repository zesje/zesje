import flask
from hashlib import md5
from webargs.flaskparser import FlaskParser
from webargs import ValidationError, fields
from werkzeug.exceptions import HTTPException


ERROR_CODE_NOT_FOUND = 404
ERROR_CODE_MALFORMED = 422
ERROR_CODE_CONFLICT = 409
ERROR_CODE_FORBIDDEN = 403
ERROR_CODE_BAD_REQUEST = 400


def abort(http_status_code, **kwargs):
    """Raise a HTTPException for the given http_status_code. Attach any keyword
    arguments to the exception for later processing.
    """
    try:
        flask.abort(http_status_code)
    except HTTPException as e:
        if len(kwargs):
            e.data = kwargs
        raise


class ApiParser(FlaskParser):

    DEFAULT_VALIDATION_STATUS = ERROR_CODE_MALFORMED
    DEFAULT_LOCATION = 'view_args'


class ApiValidationError(HTTPException):

    def __init__(self, msg, status_code=ApiParser.DEFAULT_VALIDATION_STATUS):
        super().__init__(status_code)
        self.description = msg
        self.code = status_code


ExamNotFinalizedError = ApiValidationError('Exam must be finalized', ERROR_CODE_CONFLICT)


def non_empty_string(text):
    if text is None or not text.strip():
        raise ApiValidationError("String must not be empty", ERROR_CODE_MALFORMED)


parser = ApiParser()
use_args = parser.use_args
use_kwargs = parser.use_kwargs


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
    ApiValidationError
        * `id` is not a valid integer
        * `id` is smaller than 1
        * Model with `id` does not exist in database
        * Model does not satisfy the `validate_model` requirements
    """

    def __init__(self, model, validate_model=None, **kwargs):
        super().__init__(**kwargs)
        self.model = model
        self.validate_model = validate_model

    def _validated(self, value):
        """Format the value or raise a :exc:`ValidationError` if an error occurs."""
        try:
            id = super()._validated(value)
        except ValidationError as e:
            raise ApiValidationError(e.message, ERROR_CODE_MALFORMED)

        if id < 1:  # MySQL db identifiers start at 1
            raise ApiValidationError("Id must be 1 or larger.", ERROR_CODE_MALFORMED)

        return id

    def _validate_all_model(self, item):
        if self.validate_model:
            for validator in self.validate_model:
                res = validator(item)
                if isinstance(res, ApiValidationError):
                    raise res

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
            raise ApiValidationError(f"{self.model.__name__} with id #{id} does not exist.", ERROR_CODE_NOT_FOUND)

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
