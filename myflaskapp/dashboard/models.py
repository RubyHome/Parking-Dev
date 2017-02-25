# -*- coding: utf-8 -*-
"""User models."""
import datetime as dt, hashlib
from flask_login import UserMixin
from .utils import timestamp
from myflaskapp.database import Column, Model, SurrogatePK, db, reference_col, relationship
from myflaskapp.extensions import bcrypt


class Role(SurrogatePK, Model):
    """A role for a user."""

    __tablename__ = 'roles'
    name = Column(db.String(80), unique=True, nullable=False)
    user_id = reference_col('users', nullable=True)
    user = relationship('User', backref='roles')

    def __init__(self, name, **kwargs):
        """Create instance."""
        db.Model.__init__(self, name=name, **kwargs)

    def __repr__(self):
        """Represent instance as a unique string."""
        return '<Role({name})>'.format(name=self.name)



class User(UserMixin, SurrogatePK, Model):
    """A user of the app."""

    __tablename__ = 'users'
    username = Column(db.String(80), unique=True, nullable=False)
    email = Column(db.String(80), unique=True, nullable=False)
    #: The hashed password
    password = Column(db.String(128), nullable=True)
    created_at = Column(db.DateTime, nullable=False, default=dt.datetime.utcnow)
    first_name = Column(db.String(30), nullable=True)
    last_name = Column(db.String(30), nullable=True)
    address = Column(db.String(50), nullable=True)
    active = Column(db.Boolean(), default=True)
    admin = Column(db.Boolean, nullable=False, default=False)
    confirmed = Column(db.Boolean, nullable=False, default=False)
    confirmed_on = Column(db.DateTime, nullable=True)
    confirm_code = Column(db.Unicode(50), nullable=True)
    is_banned = Column(db.Boolean(), default=False)
    phone = Column(db.Unicode(50), unique=False, nullable=True)
    #avatar_hash = Column(db.String(32))
    #last_seen_at = db.Column(db.Integer, default=timestamp)
    #online = db.Column(db.Boolean, default=False)

    def __init__(self, username, email, password=None, admin=False, confirmed_on=None, **kwargs):
        """Create instance."""
        db.Model.__init__(self, username=username, email=email, admin=admin, confirmed_on=confirmed_on, **kwargs)
        if password:
            self.set_password(password)
        else:
            self.password = None

    def gravatar_hash(self, **kwargs):
        if self.email is not None and self.avatar_hash is None:
            self.avatar_hash = hashlib.md5(
                self.email.encode('utf-8')).hexdigest()

    def gravatar(self, size=100, default='identicon', rating='g'):
        """call gravatar with size arg 1-128 user.gravatar(size=128)"""
        if request.is_secure:
            url = 'https://secure.gravatar.com/avatar'
        else:
            url = 'http://www.gravatar.com/avatar'
        hash = self.avatar_hash or \
               hashlib.md5(self.email.encode('utf-8')).hexdigest()
        return '{url}/{hash}?s={size}&d={default}&r={rating}'.format(
            url=url, hash=hash, size=size, default=default, rating=rating)

    # https://github.com/miguelgrinberg/flack/blob/master/flack/events.py
    def ping(self):
        """Marks the user as recently seen and online.
        mobile app clients must send a ping event periodically
         to keep the user online"""
        self.last_seen_at = timestamp()
        last_online = self.online
        self.online = True
        return last_online != self.online

    @staticmethod
    def find_offline_users():
        """Find users that haven't been active and mark them as offline."""
        users = User.query.filter(User.last_seen_at < timestamp() - 60,
                                  User.online == True).all()  # noqa
        for user in users:
            user.online = False
            db.session.add(user)
        db.session.commit()
        return users

    def set_password(self, password):
        """Set password."""
        self.password = bcrypt.generate_password_hash(password)

    def check_password(self, value):
        """Check password."""
        return bcrypt.check_password_hash(self.password, value)

    @property
    def full_name(self):
        """Full user name."""
        return '{0} {1}'.format(self.first_name, self.last_name)

    def __repr__(self):
        """Represent instance as a unique string."""
        return '<User({username!r})>'.format(username=self.username)
