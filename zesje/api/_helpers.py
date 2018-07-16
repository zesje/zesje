import flask_restful


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
