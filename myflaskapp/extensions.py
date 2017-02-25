# -*- coding: utf-8 -*-
"""Extensions module. Each extension is initialized in the app factory located in app.py."""
import warnings
from flask_bcrypt import Bcrypt
from flask_cache import Cache
from flask_debugtoolbar import DebugToolbarExtension
from flask_login import LoginManager
from flask_migrate import Migrate
from flask_sqlalchemy import SQLAlchemy
from flask_mail import Mail
from flask_jwt_extended import JWTManager
from celery import Celery
from twilio.rest import TwilioRestClient
from myflaskapp.settings import Config
from flask.exthook import ExtDeprecationWarning
from flask_compress import Compress

warnings.simplefilter('ignore', ExtDeprecationWarning)

bcrypt = Bcrypt()
login_manager = LoginManager()
db = SQLAlchemy()
migrate = Migrate()
cache = Cache()
debug_toolbar = DebugToolbarExtension()
flask_mail = Mail()
celery = Celery(__name__, broker=Config.CELERY_BROKER_URL, backend=Config.CELERY_RESULT_BACKEND)
client = TwilioRestClient(account='AC5763553f48cd2c29f96070cb46556707', token='bf3b287c019c2bb93d63fa3512600806')
compress = Compress()
jwtmanager = JWTManager()
