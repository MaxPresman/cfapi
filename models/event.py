from . import db
from datetime import datetime
from dateutil.tz import tzoffset
from flask import request
from sqlalchemy.orm import backref


class Event(db.Model):
    '''
        Organizations events from Meetup
    '''
    # Columns
    id = db.Column(db.Integer(), primary_key=True)
    name = db.Column(db.Unicode())
    description = db.Column(db.Unicode())
    event_url = db.Column(db.Unicode())
    location = db.Column(db.Unicode())
    created_at = db.Column(db.Unicode())
    start_time_notz = db.Column(db.DateTime(False))
    end_time_notz = db.Column(db.DateTime(False))
    utc_offset = db.Column(db.Integer())
    keep = db.Column(db.Boolean())

    # Relationships
    # child
    organization = db.relationship('Organization', single_parent=True, cascade='all, delete-orphan', backref=backref("events", cascade="save-update, delete"))
    organization_name = db.Column(db.Unicode(), db.ForeignKey('organization.name', ondelete='CASCADE'), nullable=False)

    def __init__(self, name, event_url, start_time_notz, created_at, utc_offset,
                 organization_name, location=None, end_time_notz=None, description=None):
        self.name = name
        self.description = description
        self.location = location
        self.event_url = event_url
        self.start_time_notz = start_time_notz
        self.utc_offset = utc_offset
        self.end_time_notz = end_time_notz
        self.organization_name = organization_name
        self.created_at = created_at
        self.keep = True

    def start_time(self):
        ''' Get a string representation of the start time with UTC offset.
        '''
        if self.start_time_notz is None:
            return None
        tz = tzoffset(None, self.utc_offset)
        st = self.start_time_notz
        dt = datetime(st.year, st.month, st.day, st.hour, st.minute, st.second, tzinfo=tz)
        return dt.strftime('%Y-%m-%d %H:%M:%S %z')

    def end_time(self):
        ''' Get a string representation of the end time with UTC offset.
        '''
        if self.end_time_notz is None:
            return None
        tz = tzoffset(None, self.utc_offset)
        et = self.end_time_notz
        dt = datetime(et.year, et.month, et.day, et.hour, et.minute, et.second, tzinfo=tz)
        return dt.strftime('%Y-%m-%d %H:%M:%S %z')

    def api_url(self):
        ''' API link to itself
        '''
        return '%s://%s/api/events/%s' % (request.scheme, request.host, str(self.id))

    def asdict(self, include_organization=False):
        ''' Return Event as a dictionary, with some properties tweaked.

            Optionally include linked organization.
        '''
        event_dict = db.Model.asdict(self)

        # remove fields that don't need to be public
        for key in ('keep', 'start_time_notz', 'end_time_notz', 'utc_offset'):
            del event_dict[key]

        for key in ('start_time', 'end_time', 'api_url'):
            event_dict[key] = getattr(self, key)()

        if include_organization:
            event_dict['organization'] = self.organization.asdict()

        return event_dict
