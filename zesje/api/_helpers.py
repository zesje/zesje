import flask_restful
from hashlib import md5


def nonempty_string(s):
    s = str(s)
    if not s:
        raise ValueError('cannot be an empty string')
    return s


def required_string(parser, name):
    parser.add_argument(name, type=nonempty_string,
                        required=True, nullable=False)


def abort(status, **kwargs):
    flask_restful.abort(status, status=status, **kwargs)


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
