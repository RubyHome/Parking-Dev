
from flask import Blueprint
from flask_login import login_required
from myflaskapp.parking.models import AddressEntry, AddressDistance
from myflaskapp.notify.email import check_confirmed


blueprint = Blueprint('selling', __name__)



# user update individual parking spot price

@blueprint.route('/update_price', methods=["POST"])
@login_required
#@check_confirmed
def update_price():
    """
    Not currently used, spot_id is passed in and as well as an updated price
    and saves the new price for the specified parking spot to the db.
    """
    spot_id = int(request.form.get('id'))
    price = float(request.form.get('price'))
    if request.method == 'POST':
        spot = AddressEntry.query.get(spot_id)
        spot.price = price
        spot.save()
        return str(spot_id)
