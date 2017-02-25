# -*- coding: utf-8 -*-
"""The app module, containing the app factory function."""
import os
from flask import Flask, render_template, jsonify
from flask_cors import CORS
from myflaskapp import async, auth, dashboard, parking, payment, selling
from myflaskapp.extensions import bcrypt, cache, db, debug_toolbar, login_manager, migrate, flask_mail, celery, compress, jwtmanager
from myflaskapp.settings import ProdConfig, Config as config
from flask_wtf.csrf import CsrfProtect


MAPBOX_KEY = 'pk.eyJ1Ijoiam9neW4iLCJhIjoiY2lsdHpvaGUzMDBpMHY5a3MxcDMycHltZSJ9.VhDkOW21B44br30e9Td3Pg'
os.environ['MAPBOX_ACCESS_TOKEN'] = MAPBOX_KEY
login_manager.session_protection = 'strong'
login_manager.login_view = 'auth.login'

def create_app(config_object=ProdConfig):
    """An application factory, as explained here: http://flask.pocoo.org/docs/patterns/appfactories/.

    :param config_object: The configuration object to use.
    """
    app = Flask(__name__)
    app.config.from_object(config_object)
    register_extensions(app)
    register_blueprints(app)
    register_errorhandlers(app)
    CsrfProtect(app)
    CORS(app, supports_credentials=True)
    compress.init_app(app)
    return app

def register_extensions(app):
    """Register Flask extensions."""
    bcrypt.init_app(app)
    cache.init_app(app)
    db.init_app(app)
    login_manager.init_app(app)
    debug_toolbar.init_app(app)
    migrate.init_app(app, db)
    flask_mail.init_app(app)
    celery.conf.update(app.config)
    jwtmanager.init_app(app)
    return None


def register_blueprints(app):
    """Register Flask blueprints."""
    app.register_blueprint(parking.views.blueprint)
    app.register_blueprint(async.backgroundtasks.blueprint)
    app.register_blueprint(selling.views.blueprint)
    app.register_blueprint(auth.views.blueprint)
    app.register_blueprint(payment.views.blueprint)
    return None


def register_errorhandlers(app):
    """Register error handlers."""
    def render_error(error):
        """Render error template."""
        # If a HTTPException, pull the `code` attribute; default to 500
        error_code = getattr(error, 'code', 500)
        return jsonify({'error': error}), error_code
    for errcode in [401, 404, 500]:
        app.errorhandler(errcode)(render_error)
    return None
