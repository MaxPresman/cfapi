from . import db
from flask import request
from sqlalchemy.orm import backref

class Issue(db.Model):
    '''
        Issues of Civic Tech Projects on Github
    '''
    # Columns
    id = db.Column(db.Integer(), primary_key=True)
    title = db.Column(db.Unicode())
    html_url = db.Column(db.Unicode())
    body = db.Column(db.Unicode())
    keep = db.Column(db.Boolean())

    # Relationships
    # child
    project = db.relationship('Project', single_parent=True, cascade='all, delete-orphan', backref=backref("issues", cascade="save-update, delete"))
    project_id = db.Column(db.Integer(), db.ForeignKey('project.id', ondelete='CASCADE'), nullable=False, index=True)

    # can contain labels (this relationship is defined in the child object)

    def __init__(self, title, project_id=None, html_url=None, labels=None, body=None):
        self.title = title
        self.html_url = html_url
        self.body = body
        self.project_id = project_id
        self.keep = True

    def api_url(self):
        ''' API link to itself
        '''
        return '%s://%s/api/issues/%s' % (request.scheme, request.host, str(self.id))

    def asdict(self, include_project=False):
        '''
            Return issue as a dictionary with some properties tweaked
        '''
        issue_dict = db.Model.asdict(self)

        # TODO: Also paged_results assumes asdict takes this argument, should be checked and fixed later
        if include_project:
            from . import Project

            issue_dict['project'] = db.session.query(Project).filter(Project.id == self.project_id).first().asdict()
            del issue_dict['project']['issues']
            del issue_dict['project_id']

        # remove fields that don't need to be public
        del issue_dict['keep']

        issue_dict['api_url'] = self.api_url()
        issue_dict['labels'] = [l.asdict() for l in self.labels]

        return issue_dict
