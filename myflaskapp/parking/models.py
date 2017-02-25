# -*- coding: utf-8 -*-
"""User models."""
import json
from myflaskapp.database import Column, Model, SurrogatePK, db
from marshmallow import Schema, fields, validate



class AddressDistance(SurrogatePK, Model):
    __tablename__ =  'address_distance'
    address_a_id = Column(db.ForeignKey('address.id'), unique=False, nullable=False)
    address_b_id = Column(db.ForeignKey('address.id'), unique=False, nullable=False)
    mapbox_response = Column(db.Text, nullable=False)
    speed_scala = Column(db.Integer, nullable=True) # max_distance


    @classmethod
    def get_direction_pois(cls, a_id):
        pois = []
        for result in cls.query \
            .filter(cls.address_a_id==a_id).order_by(cls.speed_scala):
            # check availability
            spot = AddressEntry.query.get(result.address_b_id)
            if spot.is_avail == False:
                continue

            pois.append({
                'address_a_id': AddressEntry.query.get(result.address_a_id).as_geojson(),
                'address_b_id': AddressEntry.query.get(result.address_b_id).as_geojson(),
                'mapbox_response': json.loads(result.mapbox_response),
                'speed_scala': result.speed_scala,
            })
        return pois


class AddressEntry(SurrogatePK, Model):
    __tablename__ = 'address'
    user_id = Column(db.ForeignKey('users.id'), unique=False, nullable=False) # Owner
    latitude = Column(db.String(80), unique=False, nullable=False)
    longitude = Column(db.String(80), unique=False, nullable=False)
    mapbox_place_name = Column(db.String(1024), unique=False, nullable=True)
    street_name = Column(db.Unicode(1024), unique=False, nullable=True)
    street_number = Column(db.Unicode(1024), unique=False, nullable=True)
    building_number = Column(db.Unicode(1024), unique=False, nullable=True)
    cross_street = Column(db.Unicode(1024), unique=False, nullable=True)
    suite_number = Column(db.Unicode(1024), unique=False, nullable=True)
    neighborhood = Column(db.Unicode(1024), unique=False, nullable=True) # mapbox.neighborhood
    district = Column(db.Unicode(1024), unique=False, nullable=True) # mapbox.place
    county = Column(db.Unicode(1024), unique=False, nullable=True)
    country = Column(db.Unicode(1024), unique=False, nullable=True) # mapbox.country
    provence = Column(db.Unicode(1024), unique=False, nullable=True)
    phone = Column(db.Unicode(10), unique=False, nullable=True)
    state = Column(db.Unicode(1024), unique=False, nullable=True) # mapbox.region

    #Sometimes postal_code comes back NULL from mapbox geocoder if it's a weird address
    #set postalcode to be nullable true to account for the weirdness
    postal_code = Column(db.Unicode(1024), unique=False, nullable=False) # mapbox.postcode
    name = Column(db.Unicode(1024), unique=False, nullable=True)
    details = Column(db.Text, unique=False, nullable=True)
    price = Column(db.Float, nullable=True)
    is_dest = Column(db.Boolean(), default=True)
    is_avail = Column(db.Boolean(), default=True)

    photo_url = Column(db.Unicode(300), unique=False, nullable=True)
    spot_type = Column(db.Unicode(50), unique=False, nullable=True)
    avail_type = Column(db.Unicode(50), unique=False, nullable=True)

    def format_phone(self, phone_raw):
        return phone_raw

    def as_geojson(self, is_dest=False):
        return {
            'type': 'Feature',
            'geometry': {
                'type': 'Point',
                # Mapbox geocoding api sends back lat long in the format of long/lat. This may have
                #  to be rendered differently for the inclusion in the mapbox map.
                'coordinates': [self.longitude, self.latitude], # match mapbox specification, t
            },
            'properties': {
                'p0': self.id,
                'p1': self.name,
                'p2': self.mapbox_place_name,
                'p4': self.phone,
                'p5': ' '.join([self.street_number or '', self.street_name or '']),
                'p6': self.state,
                'p8': self.cross_street,
                'p9': self.price,
                'marker-color': '#ff8888' if is_dest else '#66a3ff'
            }
        }


class AddressEntrySchema(Schema):
    not_blank = validate.Length(min=1, error='Field cannot be blank')
    latitude = fields.String(validate=not_blank, dump_only=True)
    longitude = fields.String(validate=not_blank, dump_only=True)
    is_avail = fields.Boolean(dump_only=True)


    class Meta:
        fields = ('id', 'latitude', 'longitude', 'mapbox_place_name', 'price')
