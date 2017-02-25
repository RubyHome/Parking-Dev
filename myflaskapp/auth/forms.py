# -*- coding: utf-8 -*-
"""Public forms."""
from flask_wtf import Form
from wtforms import PasswordField, StringField, TextField
from wtforms.validators import DataRequired, Email, Required, Length, EqualTo, ValidationError
from myflaskapp.dashboard.models import User



class LoginForm(Form):
    """Login form."""

    username = StringField('Username', validators=[DataRequired()])
    password = PasswordField('Password', validators=[DataRequired()])

    def __init__(self, *args, **kwargs):
        """Create instance."""
        super(LoginForm, self).__init__(*args, **kwargs)
        self.user = None

    def validate(self):
        """Validate the form."""
        initial_validation = super(LoginForm, self).validate()
        if not initial_validation:
            return False

        self.user = User.query.filter_by(username=self.username.data).first()
        if not self.user:
            self.username.errors.append('Unknown username')
            return False

        if not self.user.check_password(self.password.data):
            self.password.errors.append('Invalid password')
            return False

        if not self.user.active:
            self.username.errors.append('User not activated')
            return False
        return True



class RegisterForm(Form):
    """Register form."""

    username = StringField('Username',
                           validators=[DataRequired(), Length(min=3, max=25)])
    firstname = StringField('First Name',
                            validators=[DataRequired(), Length(min=2, max=15)])
    lastname = StringField('Last Name',
                            validators=[DataRequired(), Length(min=3, max=25)])
    email = StringField('Email',
                        validators=[DataRequired(), Email(), Length(min=6, max=40)])
    password = PasswordField('Password',
                             validators=[DataRequired(), Length(min=6, max=40)])
    confirm = PasswordField('Verify password',
                            [DataRequired(), EqualTo('password', message='Passwords must match')])


    def __init__(self, *args, **kwargs):
        """Create instance."""
        super(RegisterForm, self).__init__(*args, **kwargs)
        self.user = None

    def validate(self):
        """Validate the form."""
        initial_validation = super(RegisterForm, self).validate()
        if not initial_validation:
            return False
        user = User.query.filter_by(username=self.username.data).first()
        if user:
            self.username.errors.append('Username already registered')
            return False
        user = User.query.filter_by(email=self.email.data).first()
        if user:
            self.email.errors.append('Email already registered')
            return False
        return True



class EditForm(Form):
    password = PasswordField('password', validators=[DataRequired(), Length(min=6, max=40)])
    Retype_password = PasswordField('Retype_password', [DataRequired(), EqualTo('password', message='Passwords must match')])



class Update(Form):
    username = StringField('username', validators=[DataRequired(), Length(min=3, max=25)])
    email = StringField('email', validators=[DataRequired(), Email(), Length(min=6, max=40)])



class Unique(object):

    '''
    Custom validator to check an object's attribute
    is unique. For example users should not be able
    to create an account if the account's email
    address is already in the database. This class
    supposes you are using SQLAlchemy to query the
    database.
    '''

    def __init__(self, model, field, message):
        self.model = model
        self.field = field
        self.message = message

    def __call__(self, form, field):
        check = self.model.query.filter(self.field == field.data).first()
        if check:
            raise ValidationError(self.message)



class Forgot(Form):

    ''' User forgot password form. '''

    email = TextField(validators=[Required(), Email()],
                      description='Email address')



class Reset(Form):

    ''' User reset password form. '''

    password = PasswordField(validators=[
        Required(), Length(min=6),
        EqualTo('confirm', message='Passwords must match.')
    ], description='Password')
    confirm = PasswordField(description='Confirm password')
