from flask import Blueprint, jsonify, request, redirect

from . import db

app = Blueprint(__name__, __name__)
