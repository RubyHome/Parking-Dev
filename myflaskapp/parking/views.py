# -*- coding: utf-8 -*-
"""User views."""
import mapbox, json, math, requests
from flask import Blueprint, render_template, \
    request, session, jsonify, abort, g
from flask_restful import Api, Resource
from flask_login import login_required, login_user, logout_user, current_user, fresh_login_required
from flask_jwt_extended import JWTManager, jwt_required,\
    create_access_token, get_jwt_identity, jwt_refresh_token_required
from myflaskapp.dashboard.models import User
from myflaskapp.notify.mobile import send_mobile_confirm_code
from myflaskapp.parking.models import AddressEntry, AddressDistance, AddressEntrySchema
from myflaskapp.extensions import celery, login_manager, bcrypt
from myflaskapp.database import db
from myflaskapp.parking.forms import AddressEntryForm, AddressEntryCommitForm
from myflaskapp.parking.helpers import TokenResource, etag
from myflaskapp.notify.email import check_confirmed
from celery.utils.log import get_task_logger

blueprint = Blueprint('parking', __name__)
api = Api(blueprint)

logger = get_task_logger(__name__)



# Any API class now inheriting the TokenResource class will need Authentication
class BuyParking(TokenResource):
    """
    This protected endpoint contains methods for submitting an address to be
    matched and distance measured against available parking spots.
    """
    @etag
    def get(self):
        user = User.query.filter_by(email=get_jwt_identity()).first()
        g.user_id = user.id
        # If no address is saved for the current user, return an empty object.
        query_set = AddressEntry.query.filter(AddressEntry.user_id==g.user_id)
        if query_set.count() < 1:
            return jsonify({'waypoints': [], 'origin': {}, 'empty': True})

        # destination address
        address_entry = query_set.first()
        return jsonify({
            'waypoints': AddressDistance.get_direction_pois(address_entry.id),
            'origin': address_entry.as_geojson(True),
        })

    def post(self):
        user = User.query.filter_by(email=get_jwt_identity()).first()
        g.user_id = user.id
        lookup = json.loads(request.data.decode('utf-8'))['address']
        geocoder = mapbox.Geocoder()
        features = json.loads(geocoder.forward(lookup).content.decode('utf-8'))['features']

        selected_feature = None
        for feature in features:
            if 'address' in feature:
                selected_feature = feature
                break
        if not selected_feature:
            return 'Address not found', 400

        # print lookup
        # print selected_feature['place_name'], '@@@@@@@@'
        # print selected_feature['relevance']

        query_set = AddressEntry.query.filter(AddressEntry.user_id==g.user_id, AddressEntry.is_dest==True, AddressEntry.is_avail==True)
        if query_set.count() == 0:
            address_entry = AddressEntry()
            address_entry.user_id = g.user_id
            address_entry.is_dest = True
            address_entry.is_avail = True
        else:
            address_entry = query_set.first()


        address_entry.name = json.loads(request.data.decode('utf-8'))['spot_name']
        address_entry.longitude = selected_feature['center'][0]
        address_entry.latitude = selected_feature['center'][1]
        address_entry.street_number = selected_feature['address']
        address_entry.street_name = selected_feature['text']
        address_entry.mapbox_place_name = selected_feature['place_name']

        # Generate a dict from
        for feature in selected_feature['context']:
            if feature['id'].startswith('place'):
                address_entry.county = feature['text']

            if feature['id'].startswith('postcode'):
                address_entry.postal_code = feature['text']

            if feature['id'].startswith('region'):
                address_entry.state = feature['text']

            if feature['id'].startswith('country'):
                address_entry.country = feature['text']

            if feature['id'].startswith('neighborhood'):
                address_entry.neighborhood = feature['text']

        db_session = db.session()
        db_session.add(address_entry)
        db_session.commit()

        origin = {
            'type': 'Feature',
            'properties': {'name': address_entry.name},
            'geometry': {
                'type': 'Point',
                'coordinates': [float(address_entry.longitude), float(address_entry.latitude)]
            }
        }

        # just for the parking spots within the threshold (20Km), create/update the distance from the destination
        for sub_address in AddressEntry.query.filter(AddressEntry.is_dest==False, AddressEntry.is_avail==True):
            distance = get_straight_distance(float(address_entry.latitude), float(address_entry.longitude), float(sub_address.latitude), float(sub_address.longitude))
            if distance > 5000:
                continue

            query_set = AddressDistance.query.filter(AddressDistance.address_a_id==address_entry.id, AddressDistance.address_b_id==sub_address.id)
            if query_set.count() == 0:
                address_distance = AddressDistance()
            else:
                address_distance = query_set.first()

            destination = {
                'type': 'Feature',
                'properties': {'name': sub_address.name},
                'geometry': {
                    'type': 'Point',
                    'coordinates': [float(sub_address.longitude), float(sub_address.latitude)],
                }
            }

            content = mapbox.Directions().directions([origin, destination],'mapbox.driving').geojson()
            address_distance.address_a_id = address_entry.id
            address_distance.address_b_id = sub_address.id
            address_distance.mapbox_response = json.dumps(content)
            address_distance.speed_scala = sum([feature['properties']['distance'] for feature in content['features']])
            db_session = db.session()
            db_session.add(address_distance)
            db_session.commit()


        return  {
                    'waypoints': AddressDistance.get_direction_pois(address_entry.id),
                    'origin': address_entry.as_geojson(True),
                }


api.add_resource(BuyParking, '/api/v1/park')


class SellParking(TokenResource):
    """
    This protected endpoint contains methods for adding and or registering
    a parking spot for sale.
    """
    @etag
    def get(self, action):
        user = User.query.filter_by(email=get_jwt_identity()).first()
        g.user_id = user.id
        if action == 'my_spots':
            spots = AddressEntry.query.filter(AddressEntry.user_id==g.user_id, AddressEntry.is_dest==False)
            schema = AddressEntrySchema()
            spots = schema.dump(spots, many=True).data
            return jsonify(spots)
######## create valid address function
        elif action == 'is_valid_address':
            return { 'result': True }



    def post(self, action):
        user = User.query.filter_by(email=get_jwt_identity()).first()
        g.user_id = user.id
        spot = json.loads(request.data.decode('utf-8'))
        address_entry = AddressEntry()

        address_entry.user_id = g.user_id
        address_entry.is_dest = False
        address_entry.is_avail = True
        address_entry.price = spot['price']

        address_entry.photo_url = spot['photo_url']
        address_entry.spot_type = spot['spot_type']
        address_entry.avail_type = spot['availability_type']

        # update the user's phone number
        # spot['phone']

        geocoder = mapbox.Geocoder()
        features = json.loads(geocoder.forward(spot['address']).content.decode('utf-8'))['features']

        selected_feature = None
        for feature in features:
            if 'address' in feature:
                selected_feature = feature
                break
        if not selected_feature:
            return 'Requested location is not found!', 400

        address_entry.longitude = selected_feature['center'][0]
        address_entry.latitude = selected_feature['center'][1]
        address_entry.street_number = selected_feature['address']
        address_entry.street_name = selected_feature['text']
        address_entry.mapbox_place_name = selected_feature['place_name']

        # address_entry.name = data.get('name')
        # Generate a dict from
        for feature in selected_feature['context']:
            if feature['id'].startswith('place'):
                address_entry.county = feature['text']

            if feature['id'].startswith('postcode'):
                address_entry.postal_code = feature['text']

            if feature['id'].startswith('region'):
                address_entry.state = feature['text']

            if feature['id'].startswith('country'):
                address_entry.country = feature['text']

            if feature['id'].startswith('neighborhood'):
                address_entry.neighborhood = feature['text']

        db_session = db.session()
        db_session.add(address_entry)
        db_session.commit()

        origin = {
            'type': 'Feature',
            'properties': {'name': address_entry.street_name},
            'geometry': {
                'type': 'Point',
                'coordinates': [float(address_entry.longitude), float(address_entry.latitude)]
            }
        }

        # just for the destinations within the threshold (20Km), create the distance from the new spot
        for sub_address in AddressEntry.query.filter(AddressEntry.is_dest==True, AddressEntry.is_avail==True):
            distance = get_straight_distance(float(address_entry.latitude), float(address_entry.longitude), float(sub_address.latitude), float(sub_address.longitude))
            if distance > 20000:
                continue

            address_distance = AddressDistance()

            destination = {
                'type': 'Feature',
                'properties': {'name': sub_address.street_name},
                'geometry': {
                    'type': 'Point',
                    'coordinates': [float(sub_address.longitude), float(sub_address.latitude)],
                }
            }

            content = mapbox.Directions().directions([origin, destination],'mapbox.driving').geojson()
            address_distance.address_a_id = sub_address.id      # destination
            address_distance.address_b_id = address_entry.id    # parking spot
            address_distance.mapbox_response = json.dumps(content)
            address_distance.speed_scala = sum([feature['properties']['distance'] for feature in content['features']])
            db_session = db.session()
            db_session.add(address_distance)
            db_session.commit()
        return 'success'



    # should be delete but it does not allow extra data
    def patch(self, action):
        user = User.query.filter_by(email=get_jwt_identity()).first()
        g.user_id = user.id
        spot_id = json.loads(request.data.decode('utf-8'))['spot_id']
        spot = AddressEntry.query.get(spot_id)
        # delete relavant entries in distance table.
        AddressDistance.query.filter(AddressDistance.address_b_id==spot.id).delete()
        spot.delete()
        return 'success'

api.add_resource(SellParking, '/api/v1/parksell/<string:action>')



class MobileConfirm(TokenResource):
    """
    A phone number is passed in and a msg/random confirmation code is sent to the
    supplied phone number, a success object is returned.
    curl -H "Accept: application/json" \
    -H "Content-type: application/json" -X POST \
    -H "Authorization: Bearer $token" \
    -d '{"number": "+12505889595"}' \
    http://127.0.0.1:5000/api/v1/mobile_confirm

    """
    def post(self):
        user = User.query.filter_by(email=get_jwt_identity()).first()
        g.user_id = user.id
        to_number = json.loads(request.data.decode('utf-8'))['number']
        user.confirm_code = send_mobile_confirm_code(to_number)
        db.session.add(user)
        db.session.commit()
        return 'success'

api.add_resource(MobileConfirm, '/api/v1/mobile_confirm')



class MobileCodeConfirm(TokenResource):
    """
    takes the mobile_confirm code sent to the user and compares it against the one
    stored for the user in the db. Returns success or incorrect code.
    curl -H "Accept: application/json" \
    -H "Content-type: application/json" -X POST \
    -H "Authorization: Bearer $token" \
    -d '{"confirm_code": "408702"}' \
    http://127.0.0.1:5000/api/v1/mobile_code_confirm

    """
    def post(self):
        user = User.query.filter_by(email=get_jwt_identity()).first()
        g.user_id = user.id
        confirm_code = json.loads(request.data.decode('utf-8'))['confirm_code']
        if confirm_code == user.confirm_code:
            return 'success'
        else:
            return 'incorrect code', 400


api.add_resource(MobileCodeConfirm, '/api/v1/mobile_code_confirm')




class ReverseGeo(TokenResource):
    """
    In progress:
    This protected endoint accepts a longitude and latitude and returns
    surrounding points of interest.
    example: posting Uvics lon/lat

    curl \
    -H "Accept: application/json" \
    -H "Content-type: application/json" -X POST \
    -H "Authorization: Bearer $token" \
    -d '{"lon": "-123.313465", "lat": "48.461777"}' \
    http://localhost:5000/api/v1/reverse_geo

    Both forward() and reverse() can be restricted to one or more place types.
    response = geocoder.reverse(lon=-73.989, lat=40.733, types=['poi'])
    features = response.geojson()['features']
    all([f['id'].startswith('poi') for f in features])
    """
    def post(self):
        user = User.query.filter_by(email=get_jwt_identity()).first()
        g.user_id = user.id
        lon = json.loads(request.data.decode('utf-8'))['lon']
        lat = json.loads(request.data.decode('utf-8'))['lat']
        geocoder = mapbox.Geocoder()
        response = geocoder.reverse(lon, lat)

        #if response.status_code == 200:
        #    for f in response.geojson()['features']:
        #        print('{place_name}: {id}'.format(**f))

        features = response.geojson()['features']
        if response.status_code == 200:
            return features, 200
        else:
            return 'could not complete the request', 400

api.add_resource(ReverseGeo, '/api/v1/reverse_geo')




# returns available spots geojson
class Longlat(TokenResource):
    """
    This protected endpoint returns the lng/lat of available parking spots
    without user specific context.
    """
    @etag
    def get(self):
        try:
            schema = AddressEntrySchema()
            results = AddressEntry.query.filter_by(is_avail=True, is_dest=False)
            longlat = schema.dump(results, many=True).data
            return jsonify({"longlat": longlat})
        except:
            return jsonify({"msg": "error"}), 401

api.add_resource(Longlat, '/api/v1/geojson')



##########
##########



def get_straight_distance(lat1, lon1, lat2, lon2):
    '''
    calculates the distance between two gps positions (latitude, longitude)
    takes the lat/lng of two points and returns the distance between them
    in meters.
    '''
    R = 6371  # Radius of the earth in km
    dLat = math.radians(lat2-lat1)  # deg2rad below
    dLon = math.radians(lon2-lon1)
    a = math.sin(dLat/2) * math.sin(dLat/2) + math.cos(math.radians(lat1)) * math.cos(math.radians(lat2)) * math.sin(dLon/2) * math.sin(dLon/2)

    c = 2 * math.atan2(math.sqrt(a), math.sqrt(1-a))
    return R * c * 1000 # Distance in m
