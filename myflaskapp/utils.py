# -*- coding: utf-8 -*-
"""Helper utilities and decorators."""
from flask import flash, jsonify, Blueprint, request


api = Blueprint('api', __name__)

# jinja2 template flash errors
def flash_errors(form, category='warning'):
    """Flash all errors for a form."""
    for field, errors in form.errors.items():
        for error in errors:
            flash('{0} - {1}'.format(getattr(form, field).label.text, error), category)


def bad_request(message):
    response = jsonify({'error': 'bad request', 'message': message})
    response.status_code = 400
    return response


def not_found_error(e):
    response = jsonify({'error': 'not found', 'message': message})
    response.status_code = 404
    return response


@api.errorhandler(KeyError)
def validation_error(e):
    return bad_request(e.args[0])


@api.errorhandler(404)
def not_found_error(e):
    return not_found(e.args[0])
