import stripe
from flask import Blueprint, request, render_template
from flask_login import login_required, current_user, fresh_login_required
from myflaskapp.parking.models import AddressEntry
from myflaskapp.notify.email import check_confirmed
#billing
#test card = 4242 4242 4242 4242, 10/2018, 123

blueprint = Blueprint('payment', __name__)


stripe_keys = {
    'stripe_secret_key': 'sk_test_Lu2XXzNk4NTCpml4LTJeP9nv',
    'publishable_key': 'pk_test_LZD0hxNPL2niArcUwTE3GyDH'
}

stripe.api_key = stripe_keys['stripe_secret_key']

"""
stripe.api_base = "https://api-tls12.stripe.com"

if stripe.VERSION in ("1.13.0", "1.14.0", "1.14.1", "1.15.1", "1.16.0", "1.17.0", "1.18.0", "1.19.0"):
  print("Bindings update required.")

try:
  stripe.Charge.all()
  print("TLS 1.2 supported, no action required.")
except stripe.error.APIConnectionError:
  print("TLS 1.2 is not supported. You will need to upgrade your integration.")
"""



@blueprint.route('/charge_initial')
@login_required
#@check_confirmed
def charge_initial():
    """
    Not currently in use, parking spot id gets passed in and it carries over
    and passes it into the stripe charge view.
    """
    spot_id = int(request.args.get('id'))
    spot = AddressEntry.query.get(spot_id)
    return render_template('users/charge_initial.html', key=stripe_keys['publishable_key'], price=spot.price)



@blueprint.route('/charge', methods=['POST'])
@login_required
#@check_confirmed
def charge():
    """
    Not currently in user, charge takes the amount related to the parking spot ID
    and creates a charge for the parking spot purchase. 
    """
    # Amount in cents
    amount = int(request.form.get('amount')[:-2])
    customer = stripe.Customer.create(
        email=request.form['stripeEmail'],
        card=request.form['stripeToken'],
    )
    try:
        charge = stripe.Charge.create(
            customer=customer.id,
            amount=amount,
            currency='usd',
            description='Parking Spot purchase'
        )
        pass

    except stripe.error.CardError as e:
        return """<html><body><h1>Card Declined</h1><p>Your chard could not
        be charged. Please check the number and/or contact your credit card
        company.</p></body></html>"""
    return render_template('users/charge.html', amount=amount)
