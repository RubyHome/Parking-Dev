# -*- coding: utf-8 -*-
"""Public section, including homepage and signup."""
import datetime, json, uuid, requests
from flask import Blueprint, flash, redirect, render_template, request, url_for, jsonify, session, g, abort
from flask_login import login_required, login_user, logout_user, current_user, fresh_login_required
from flask_jwt_extended import JWTManager, jwt_required,\
    create_access_token, create_refresh_token, get_jwt_identity, jwt_refresh_token_required
from flask_restful import Api, Resource
from myflaskapp.database import db
from myflaskapp.extensions import login_manager, bcrypt
from myflaskapp.auth.forms import LoginForm, RegisterForm, EditForm, Update, Reset, Forgot
from myflaskapp.dashboard.models import User
from myflaskapp.parking.helpers import TokenResource
from myflaskapp.notify.email import check_confirmed, generate_confirmation_token, confirm_token
from myflaskapp.utils import flash_errors
from myflaskapp.async.backgroundtasks import send_mailgun_email
from itsdangerous import URLSafeTimedSerializer


blueprint = Blueprint('auth', __name__)
api = Api(blueprint)
ts = URLSafeTimedSerializer('Secretfuckingkeyseverywhere')



#API Register
class Register(Resource):
    def post(self):
        """
        This endpoint takes a the user properties from the angular register form
        and registers a new user, currently it sends an api key back as a convenience
        method for development. *The token should be
        removed in the future as email confirmation has to take place first.
        """
        json_data = request.json
        user = User(
            username=json_data['username'],
            email=json_data['email'],
            password=json_data['password']
        )
        try:
            db.session.add(user)
            db.session.commit()
            status = 'success'
        except:
            status = 'this user is already registered'
        return jsonify({'result': status})

api.add_resource(Register, '/api/v1/register')



class LoginUser(Resource):
    def post(self):
        """
        This endpoint takes the login data from the Angular login form
        and returns a token or a login error
        """
        json_data = request.json
        user = User.query.filter_by(email=json_data['email']).first()
        if user is not None and bcrypt.check_password_hash(user.password, json_data['password']):
            status = True
            ret = {
                'token': create_access_token(identity=user.email, fresh=True),
                'refresh_token': create_refresh_token(identity=user.email)
            }
            return jsonify(ret)
        else:
            status = False
            return 'email or password is incorrect', 400

        return jsonify({'result': status})

api.add_resource(LoginUser, '/api/v1/login')



class Refresh(Resource):
    """
    This protected endoint accepts a refresh token type only, verifies it then
    creates and returns a new short lived fresh access token.
    Refresh tokens can only access this endpoint and no other.
    """
    @jwt_refresh_token_required
    def post(self):
        user = User.query.filter_by(email=get_jwt_identity()).first()
        ret = {'token': create_access_token(identity=user.email)}
        return jsonify(ret)

api.add_resource(Refresh, '/api/v1/refresh')


######

""" below > older endpoints waiting to be transformed into api resources"""

######


@blueprint.route('/resend')
@login_required
def resend_confirmation():
    """
    not currently in use, previously this was used to get the current user
    connecting via session cookie and is_authenticated and send them an
    email with a fresh email confirmation token.
    """

    token = generate_confirmation_token(current_user.email)
    confirm_url = url_for('auth.confirm_email', token=token, _external=True)
    html = render_template('public/email_templates/confirm.html', confirm_url=confirm_url)
    subject = "Please confirm your email"
    send_mailgun_email.delay(current_user.email, subject, html)
    flash('A new confirmation email has been sent.', 'success')
    return redirect(url_for('auth.unconfirmed'))



@blueprint.route('/confirm/<token>')
def confirm_email(token):
    """
    not currently used, the confirm endpoint parses the passed in token
    and confirms the newly registered account and handles some cases.
    """
    try:
        email = confirm_token(token)
    except:
        flash('The confirmation link is invalid or has expired.', 'danger')
    user = User.query.filter_by(email=email).first_or_404()
    if user.confirmed:
        flash('Account already confirmed. Please login.', 'success')
    else:
        user.confirmed = True
        user.active= True
        user.confirmed_on = datetime.datetime.now()
        db.session.add(user)
        db.session.commit()
        flash('You have confirmed your account. Thanks!', 'success')
    return redirect(url_for('auth.home'))



@blueprint.route('/forgot', methods=['GET', 'POST'])
def forgot():
    """
    Not currently in use, creates a password reset token and emails it to the user

    """
    form = Forgot()
    if form.validate_on_submit():
        user = User.query.filter_by(email=form.email.data).first()
        # Check the user exists
        if user is not None:
            # Subject of the confirmation email
            subject = 'Reset your password.'
            token = ts.dumps(user.email, salt='password-reset-key')
            resetUrl = url_for('auth.reset', token=token, _external=True)
            html = render_template('public/email_templates/reset_password.html', reset_url=resetUrl)
            send_mailgun_email.delay(user.email, subject, html)
            # Send back to the home page
            return redirect(url_for('auth.home'))
            flash('Check your email to reset your password.', 'positive')
        else:
            flash('Unknown email address.', 'danger')
            return redirect(url_for('auth.forgot'))
    return render_template('/public/forgot.html', form=form)



@blueprint.route('/reset/<token>', methods=['GET', 'POST'])
def reset(token):
    """
    not currently in use, after an password reset token is passed in and parsed
    a password reset template/form was being provided to the user in order to
    complete a password reset.
    """
    try:
        email = ts.loads(token, salt='password-reset-key', max_age=1000)
    # The token can either expire or be invalid
    except:
        abort(404)
    form = Reset()
    if form.validate_on_submit():
        user = User.query.filter_by(email=email).first()
        # Check the user exists
        if user is not None:
            user.password = form.password.data
            # Update the database with the user
            user.set_password(form.password.data)
            db.session.add(user)
            db.session.commit()
            # Send to the signin page
            flash('Your password has been reset, you can sign in.', 'positive')
            return redirect(url_for('auth.home'))
        else:
            flash('Unknown email address.', 'warning')
            return redirect(url_for('auth.forgot'))
    return render_template('public/reset_password.html', form=form, token=token)



@blueprint.route('/register/', methods=['GET', 'POST'])
def register_old():
    """
    Not currently in use, old register user view.

    """
    form = RegisterForm(request.form, csrf_enabled=False)
    if form.validate_on_submit():
        user = User.create(username=form.username.data, email=form.email.data, password=form.password.data,
                    first_name=form.firstname.data, last_name=form.lastname.data, active=True, confirmed=False)
        email = form.email.data
        token = generate_confirmation_token(email)
        confirm_url = url_for('auth.confirm_email', token=token, _external=True)
        html = render_template('public/email_templates/confirm.html', confirm_url=confirm_url)
        subject = "Please confirm your email"
        send_mailgun_email.delay(email, subject, html)

        login_user(user)

        flash('Thank you for registering, a confirmation email has been sent', 'success')
        return redirect(url_for('auth.unconfirmed'))

    else:
        flash_errors(form)
    return render_template('public/register.html', form=form)


#update user details

@blueprint.route('/update_password', methods=['GET','POST'])
@fresh_login_required
#@check_confirmed
def update():
    """
    not currently in use, previously was used to have a user update
    their username despite the name of the endpoint
    if their id was in session and logged_in and is_authenticated were True
    """
    form = Update()
    if request.method == 'POST':
        g.user = User.query.get(session['user_id'])
        g.user.username = request.form['username']
        g.user.email = request.form['email']
        db.session.add(g.user)
        db.session.commit()
        flash('User Details updated')
    return render_template('users/updateuserdetails.html', form=form)



# reset password

@blueprint.route('/resetpassword', methods=['GET','POST'] )
@fresh_login_required
#@check_confirmed
def resetpassword():
    """
    not in use, previously this was used to reset the users password
    if their user_id was in session and logged_in and is_authenticated were
    True.
    """
    #if 'user_id' in session:
    form = EditForm()
    if request.method == 'POST':
        g.user = User.query.get(session['user_id'])
        if form.password.data == '':
            flash('invalid password')
        elif form.password.data == form.Retype_password.data:
            g.user.set_password(form.password.data)
            db.session.add(g.user)
            db.session.commit()
            flash('User password updated')
        else:
            flash('Check your password.')
    return render_template('users/resetpassword.html', form=form )
