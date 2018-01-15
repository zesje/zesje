from flask import Blueprint, jsonify, request, redirect

from . import db

app = Blueprint(__name__, __name__)

@app.route('/students', methods=['GET'])
@db.session
def get_students():
    return jsonify([
        dict(id=s.id, first_name=s.first_name,
             last_name=s.last_name, email=s.email)
        for s in db.Student.select()
    ])
