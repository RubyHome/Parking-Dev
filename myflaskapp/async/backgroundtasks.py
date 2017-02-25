# -*- coding: utf-8 -*-
import requests
from flask import Blueprint
from flask_mail import Message
from myflaskapp.extensions import celery


blueprint = Blueprint('async', __name__)

"""
celery example
after starting celery from the project root with

celery worker -A celery_worker.celery --loglevel=info

@celery.task(name='test_async_add_muh_nums')
def add():
    return 4 + 5

@blueprint.route('/test_async', methods=['GET'])
def add_delay():
    nums = add.delay()
    return render_template('public/home.html', nums=nums)
"""



#Send email using flask-mail
@celery.task(name='@login_SendFlaskEmail')
def send_email(to, subject, template):
    """
    if mailgun's api goes down failover to flask-mail
    takes to/from email and an email template.
    """
    msg = Message(
        subject,
        recipients=[to],
        html=template,
        sender=''
    )
    mail.send(msg)



#Send email using Mailgun Api
@celery.task(name='@login_SendMailgunEmail')
def send_mailgun_email(to, subject, template):
    """
    primary email sending, takes to/from email and an email template.
    """
    return requests.post(
        "https://api.mailgun.net/v3/app.parkable.ch/messages",
        auth=("api", "key-773add185ebcc24810d9b6bb3c2589bb"),
        data={"from": "Parkable <mailgun@app.parkable.ch>",
              "to": [to],
              "subject": subject,
              "html": template})
