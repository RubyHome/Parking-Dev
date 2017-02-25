# -*- coding: utf-8 -*-
"""User forms."""
from flask_wtf import Form
from wtforms import StringField
from wtforms.validators import DataRequired



class AddressEntryForm(Form):
    building_name = StringField('building_name')
    phone = StringField('phone')
    address = StringField('address', validators=[DataRequired()])
    city = StringField('city', validators=[DataRequired()])
    state = StringField('state', validators=[DataRequired()])
    postal_code = StringField('postal_code')
    price = StringField('price')
    form_state = StringField('form_state', validators=[DataRequired()])



class AddressEntryCommitForm(Form):
    picked = StringField('picked')
    form_state = StringField('form_state', validators=[DataRequired()])
