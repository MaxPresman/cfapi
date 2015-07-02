from . import db
from flask import request
from sqlalchemy.orm import backref

class Story(db.Model):
    '''
        Blog posts from a Brigade.
    '''
    # Columns
    id = db.Column(db.Integer(), primary_key=True)
    title = db.Column(db.Unicode())
    link = db.Column(db.Unicode())
    type = db.Column(db.Unicode())
    keep = db.Column(db.Boolean())

    # Relationships
    # child
    organization = db.relationship('Organization', single_parent=True, cascade='all, delete-orphan', backref=backref("stories", cascade="save-update, delete"))
    organization_name = db.Column(db.Unicode(), db.ForeignKey('organization.name', ondelete='CASCADE'), nullable=False)

    def __init__(self, title=None, link=None, type=None, organization_name=None):
        self.title = title
        self.link = link
        self.type = type
        self.organization_name = organization_name
        self.keep = True

    def api_url(self):
        ''' API link to itself
        '''
        return '%s://%s/api/stories/%s' % (request.scheme, request.host, str(self.id))

    def asdict(self, include_organization=False):
        ''' Return Story as a dictionary, with some properties tweaked.

            Optionally include linked organization.
        '''
        story_dict = db.Model.asdict(self)

        # remove fields that don't need to be public
        del story_dict['keep']

        story_dict['api_url'] = self.api_url()

        if include_organization:
            story_dict['organization'] = self.organization.asdict()

        return story_dict
