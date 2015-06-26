from . import db
from flask import request
from sqlalchemy import desc, DDL, event
from column_types import TSVectorType
from . import Project, Event, Story
from datetime import date, datetime
import time

from utils.name_utils import safe_name

class Organization(db.Model):
    '''
        Brigades and other civic tech organizations
    '''
    # Columns
    name = db.Column(db.Unicode(), primary_key=True)
    website = db.Column(db.Unicode())
    events_url = db.Column(db.Unicode())
    rss = db.Column(db.Unicode())
    projects_list_url = db.Column(db.Unicode())
    type = db.Column(db.Unicode())
    city = db.Column(db.Unicode())
    latitude = db.Column(db.Float())
    longitude = db.Column(db.Float())
    last_updated = db.Column(db.Integer())
    started_on = db.Column(db.Unicode())
    keep = db.Column(db.Boolean())
    tsv_body = db.Column(TSVectorType())

    # Relationships
    # can contain events, stories, projects (these relationships are defined in the child objects)

    def __init__(self, name, website=None, events_url=None,
                 rss=None, projects_list_url=None, type=None, city=None, latitude=None, longitude=None, last_updated=time.time()):
        self.name = name
        self.website = website
        self.events_url = events_url
        self.rss = rss
        self.projects_list_url = projects_list_url
        self.type = type
        self.city = city
        self.latitude = latitude
        self.longitude = longitude
        self.keep = True
        self.last_updated = last_updated
        self.started_on = unicode(date.today())

    def current_events(self):
        '''
            Return the two soonest upcoming events
        '''
        filter_old = Event.start_time_notz >= datetime.utcnow()
        current_events = Event.query.filter_by(organization_name=self.name)\
            .filter(filter_old).order_by(Event.start_time_notz.asc()).limit(2).all()
        current_events_json = [row.asdict() for row in current_events]
        return current_events_json

    def current_projects(self):
        '''
            Return the three most current projects
        '''
        current_projects = Project.query.filter_by(organization_name=self.name).order_by(desc(Project.last_updated)).limit(3)
        current_projects_json = [project.asdict(include_issues=False) for project in current_projects]

        return current_projects_json

    def current_stories(self):
        '''
            Return the two most current stories
        '''
        current_stories = Story.query.filter_by(organization_name=self.name).order_by(desc(Story.id)).limit(2).all()
        current_stories_json = [row.asdict() for row in current_stories]
        return current_stories_json

    def all_events(self):
        ''' API link to all an orgs events
        '''
        # Make a nice org name
        organization_name = safe_name(self.name)
        return '%s://%s/api/organizations/%s/events' % (request.scheme, request.host, organization_name)

    def upcoming_events(self):
        ''' API link to an orgs upcoming events
        '''
        # Make a nice org name
        organization_name = safe_name(self.name)
        return '%s://%s/api/organizations/%s/upcoming_events' % (request.scheme, request.host, organization_name)

    def past_events(self):
        ''' API link to an orgs past events
        '''
        # Make a nice org name
        organization_name = safe_name(self.name)
        return '%s://%s/api/organizations/%s/past_events' % (request.scheme, request.host, organization_name)

    def all_projects(self):
        ''' API link to all an orgs projects
        '''
        # Make a nice org name
        organization_name = safe_name(self.name)
        return '%s://%s/api/organizations/%s/projects' % (request.scheme, request.host, organization_name)

    def all_issues(self):
        '''API link to all an orgs issues
        '''
        # Make a nice org name
        organization_name = safe_name(self.name)
        return '%s://%s/api/organizations/%s/issues' % (request.scheme, request.host, organization_name)

    def all_stories(self):
        ''' API link to all an orgs stories
        '''
        # Make a nice org name
        organization_name = safe_name(self.name)
        return '%s://%s/api/organizations/%s/stories' % (request.scheme, request.host, organization_name)

    def api_id(self):
        ''' Return organization name made safe for use in a URL.
        '''
        return safe_name(self.name)

    def api_url(self):
        ''' API link to itself
        '''
        return '%s://%s/api/organizations/%s' % (request.scheme, request.host, self.api_id())

    def asdict(self, include_extras=False):
        ''' Return Organization as a dictionary, with some properties tweaked.

            Optionally include linked projects, events, and stories.
        '''
        organization_dict = db.Model.asdict(self)

        # remove fields that don't need to be public
        del organization_dict['keep']
        del organization_dict['tsv_body']

        for key in ('all_events', 'all_projects', 'all_stories', 'all_issues',
                    'upcoming_events', 'past_events', 'api_url'):
            organization_dict[key] = getattr(self, key)()

        if include_extras:
            for key in ('current_events', 'current_projects', 'current_stories'):
                organization_dict[key] = getattr(self, key)()

        return organization_dict


tbl = Organization.__table__
# Index the tsvector column
db.Index('index_org_tsv_body', tbl.c.tsv_body, postgresql_using='gin')

# Trigger to populate the search index column
trig_ddl = DDL("""
    CREATE TRIGGER tsvupdate_orgs_trigger BEFORE INSERT OR UPDATE ON organization FOR EACH ROW EXECUTE PROCEDURE tsvector_update_trigger(tsv_body, 'pg_catalog.english', name);
""")
# Initialize the trigger after table is created
event.listen(tbl, 'after_create', trig_ddl.execute_if(dialect='postgresql'))
