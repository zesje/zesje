import json

from flask import Blueprint, Response, jsonify, request, abort

from . import db

app = Blueprint(__name__, __name__)

# TODO: when making new database structure, have only a single
#       'name' field: it is just an identifier

@app.route('/graders', methods=['GET'])
@db.session
def get_graders():
    """get all graders.


    Returns
    -------
    list of:
        id: int
        first_name: str
        last_name: str
    """

    return jsonify([
        dict(id=g.id, first_name=g.first_name, last_name=g.last_name)
        for g in db.Grader.select()
    ])


@app.route('/graders', methods=['POST'])
@db.session
def post_graders():
    """add a grader.

    Parameters
    ----------
    first_name: str
    last_name: str

    Returns
    -------
    id: int
    first_name: str
    last_name: str
    """
    grader_spec = request.get_json(silent=False, force=True)
    try:
        new_grader = db.Grader(first_name=grader_spec['first_name'],
                               last_name=grader_spec['last_name'])
        db.orm.commit()
    except KeyError:
        abort(400)

    return jsonify({
        'id': new_grader.id,
        'first_name': grader_spec['first_name'],
        'last_name': grader_spec['last_name'],
    })
