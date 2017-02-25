# -*- coding: utf-8 -*-
"""Application configuration."""
import os, datetime
import simplekv.memory

class Config(object):
    """Base configuration."""

    #SECRET_KEY = os.environ.get('MYFLASKAPP_SECRET', 'secret-key')  # TODO: Change me
    SECRET_KEY = '9674e805d1c64ac70132f43d982c474681793f3b3e59c6066128542f1d470962461a1eae' #csrf
    EMAIL_KEY = 'JWcnq7E5KnFvCJ7wpFasN8RAbn2mG14VmlEGqv4HkaPSRxdCLfXeNDdXVuy03Cji' # email verification url server sign
    EMAIL_SALT = '5yWHy0BJhZHsmztTgEWBN85e1pfcST0NeRqHgZnYbpReX65C8zHEuf7Ll5JDcRMK'# email verification url server salt
    API_SALT = 'rZaz0baIqkRcGgHJkF3wlrIr3MSXlfuxZn0FFyGJcDIwehSaaMxk7IgoiHeG3XLy'  # api server signature for signing tokens.
    APP_DIR = os.path.abspath(os.path.dirname(__file__))  # This directory
    PROJECT_ROOT = os.path.abspath(os.path.join(APP_DIR, os.pardir))
    BCRYPT_LOG_ROUNDS = 13
    ASSETS_DEBUG = False
    DEBUG_TB_ENABLED = False  # Disable Debug toolbar
    DEBUG_TB_INTERCEPT_REDIRECTS = False
    CACHE_TYPE = 'simple'  # Can be "memcached", "redis", etc.
    SQLALCHEMY_TRACK_MODIFICATIONS = False
    MAPBOX_ACCESS_TOKEN = 'pk.eyJ1Ijoiam9neW4iLCJhIjoiY2lsdHpvaGUzMDBpMHY5a3MxcDMycHltZSJ9.VhDkOW21B44br30e9Td3Pg'

    #jwt
    JWT_BLACKLIST_ENABLED = True
    JWT_BLACKLIST_STORE = simplekv.memory.DictStore()
    JWT_BLACKLIST_TOKEN_CHECKS = 'refresh'
    JWT_ACCESS_TOKEN_EXPIRES = datetime.timedelta(minutes=30)

    # mail settings
    MAIL_SERVER = 'smtp.gmail.com'
    MAIL_PORT = 587
    MAIL_USE_TLS = True
    MAIL_USE_SSL = False
    # gmail authentication
    MAIL_USERNAME = ''
    MAIL_PASSWORD = ''
    # mail accounts
    MAIL_DEFAULT_SENDER = ''

    # async celery -enable fernet encryption
    CELERY_BROKER_URL = 'amqp://guest:@127.0.0.1:5672//'
    CELERY_RESULT_BACKEND = 'amqp://guest:@127.0.0.1:5672//'

    #mobile
    TWILIO_ACCOUNT_SID = 'AC5763553f48cd2c29f96070cb46556707'
    TWILIO_AUTH_TOKEN = 'bf3b287c019c2bb93d63fa3512600806'
    TWILIO_NUMBER = '+12048099756'

    #compression
    COMPRESS_MIMETYPES = 'application/json'
    COMPRESS_LEVEL = 6
    COMPRESS_MIN_SIZE = 500

class ProdConfig(Config):
    """Production configuration."""

    ENV = 'prod'
    DEBUG = False
    SQLALCHEMY_DATABASE_URI = 'postgres://rsabrgeoknimft:XEkvI6vNbQp7D20xrK-Cklr8xo@ec2-204-236-228-77.compute-1.amazonaws.com:5432/dck08qjrmev1uv'  # TODO: Change me
    DEBUG_TB_ENABLED = False  # Disable Debug toolbar
    SESSION_COOKIE_SECURE = True
    SESSION_COOKIE_HTTPONLY = True
    WTF_CSRF_ENABLED = True
    BCRYPT_LOG_ROUNDS = 13

class DevConfig(Config):
    """Development configuration."""

    ENV = 'dev'
    DEBUG = True
    DB_NAME = 'dev.db'
    # Put the db file in project root
    DB_PATH = os.path.join(Config.PROJECT_ROOT, DB_NAME)
    SQLALCHEMY_DATABASE_URI = 'sqlite:///{0}'.format(DB_PATH) # memorydb 'sqlite://'
    DEBUG_TB_ENABLED = True
    CACHE_TYPE = 'simple'  # Can be "simple", "memcached", "redis", etc.
    WTF_CSRF_ENABLED = False
    TRAP_HTTP_EXCEPTIONS = True


class TestConfig(Config):
    """Test configuration."""

    TESTING = True
    DEBUG = True
    SQLALCHEMY_DATABASE_URI = 'sqlite://'
    BCRYPT_LOG_ROUNDS = 4  # For faster tests; needs at least 4 to avoid "ValueError: Invalid rounds"
    WTF_CSRF_ENABLED = False  # Allows form testing
