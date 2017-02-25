# -*- coding: utf-8 -*-
from flask import redirect, url_for
from flask_login import current_user
from itsdangerous import URLSafeTimedSerializer
from myflaskapp.extensions import Mail
from myflaskapp.settings import Config as config
from functools import wraps


mail = Mail()

# email confirmation at signup token and email
def generate_confirmation_token(email):
    """
    email get's passed in and returns a salted email confirmation key
    """
    serializer = URLSafeTimedSerializer(config.EMAIL_KEY)
    return serializer.dumps(email, salt=config.EMAIL_SALT)



# parse token and return the confirmed email of the user
def confirm_token(token, expiration=3600):
    """
    Not currently used, decodes the email confirmation token, returns the email
    in order to confirm the user on signup.
    """
    serializer = URLSafeTimedSerializer(config.EMAIL_KEY)
    try:
        email = serializer.loads(
            token,
            salt=config.EMAIL_SALT,
            max_age=expiration
            )
    except:
        return False
    return email



# email confirmation decorator for user views.
def check_confirmed(func):
    """
    Not currently used, check if the user has confirmed their email before_request
    decorator
    """
    @wraps(func)
    def decorated_function(*args, **kwargs):
        if current_user.confirmed is False:
            return redirect(url_for('auth.unconfirmed'))
        return func(*args, **kwargs)

    return decorated_function
