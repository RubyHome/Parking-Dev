import random
from myflaskapp.extensions import client


def send_mobile_confirm_code(to_number):
    verification_code = generate_mobile_confirm_code()
    send_mobile_confirm_sms(to_number, verification_code)
    return verification_code


def generate_mobile_confirm_code():
    return str(random.randrange(100000, 999999))


def send_mobile_confirm_sms(to_number, body):
    twilio_number = '+12048099756'
    client.sms.messages.create(to=to_number,
                           from_=twilio_number,
                           body="Please enter the following confirmation code in order to confirm your account > " + body)
    return body
