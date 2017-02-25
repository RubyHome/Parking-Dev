# -*- coding: utf-8 -*-
import os, jwt, uuid, hashlib
from functools import wraps
from jwt import DecodeError, ExpiredSignature
from datetime import datetime, timedelta
from flask import Blueprint, g, jsonify, request, make_response, session
from flask_restful import Resource, Api
from flask_jwt_extended import jwt_required
from myflaskapp.dashboard.models import User
from myflaskapp.parking.models import AddressEntry, AddressEntrySchema
from myflaskapp.extensions import bcrypt
from .errors import precondition_failed, not_modified
from myflaskapp.settings import Config as config

"""The soon to be decorator factory"""
# Adding the login token decorator to the Resource class
class TokenResource(Resource):
    method_decorators = [jwt_required]


def etag(f):
    @wraps(f)
    def wrapped(*args, **kwargs):
        # only for HEAD and GET requests
        assert request.method in ['HEAD', 'GET'],\
            '@etag is only supported for GET requests'
        rv = f(*args, **kwargs)
        rv = make_response(rv)
        etag = '"' + hashlib.md5(rv.get_data()).hexdigest() + '"'
        rv.headers['ETag'] = etag
        if_match = request.headers.get('If-Match')
        if_none_match = request.headers.get('If-None-Match')
        if if_match:
            etag_list = [tag.strip() for tag in if_match.split(',')]
            if etag not in etag_list and '*' not in etag_list:
                rv = precondition_failed()
        elif if_none_match:
            etag_list = [tag.strip() for tag in if_none_match.split(',')]
            if etag in etag_list or '*' in etag_list:
                rv = not_modified()
        return rv
    return wrapped


def cache_control(*directives):
    def decorator(f):
        @wraps(f)
        def wrapped(*args, **kwargs):
            rv = f(*args, **kwargs)
            rv = make_response(rv)
            rv.headers['Cache-Control'] =', '.join(directives)
            return rv
        return wrapped
    return decorator


def no_cache(f):
    return cache_control('no-cache', 'no-store', 'max-age=0')(f)
