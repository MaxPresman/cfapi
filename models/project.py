from . import db
from . import Issue
from sqlalchemy import event, DDL

from column_types import JsonType, TSVectorType
from sqlalchemy.orm import backref
from flask import request

class Project(db.Model):
    '''
        Civic tech projects on GitHub
    '''
    # Columns
    id = db.Column(db.Integer(), primary_key=True)
    name = db.Column(db.Unicode())
    code_url = db.Column(db.Unicode())
    link_url = db.Column(db.Unicode())
    description = db.Column(db.Unicode())
    type = db.Column(db.Unicode())
    categories = db.Column(db.Unicode())
    tags = db.Column(db.Unicode())
    github_details = db.Column(JsonType())
    last_updated = db.Column(db.DateTime())
    last_updated_issues = db.Column(db.Unicode())
    last_updated_civic_json = db.Column(db.Unicode())
    last_updated_root_files = db.Column(db.Unicode())
    keep = db.Column(db.Boolean())
    tsv_body = db.Column(TSVectorType())
    status = db.Column(db.Unicode())

    # Relationships
    # child
    organization = db.relationship('Organization', single_parent=True, cascade='all, delete-orphan', backref=backref("projects", cascade="save-update, delete"))
    organization_name = db.Column(db.Unicode(), db.ForeignKey('organization.name', ondelete='CASCADE'), nullable=False)

    # can contain issues (this relationship is defined in the child object)

    def __init__(self, name, code_url=None, link_url=None,
                 description=None, type=None, categories=None, tags=None,
                 github_details=None, last_updated=None, last_updated_issues=None,
                 last_updated_civic_json=None, last_updated_root_files=None, organization_name=None,
                 keep=None, status=None):
        self.name = name
        self.code_url = code_url
        self.link_url = link_url
        self.description = description
        self.type = type
        self.categories = categories
        self.tags = tags
        self.github_details = github_details
        self.last_updated = last_updated
        self.last_updated_issues = last_updated_issues
        self.last_updated_civic_json = last_updated_civic_json
        self.last_updated_root_files = last_updated_root_files
        self.organization_name = organization_name
        self.keep = True
        self.status = status

    def api_url(self):
        ''' API link to itself
        '''
        return '%s://%s/api/projects/%s' % (request.scheme, request.host, str(self.id))

    def asdict(self, include_organization=False, include_issues=True):
        ''' Return Project as a dictionary, with some properties tweaked.

            Optionally include linked organization.
        '''
        project_dict = db.Model.asdict(self)

        # remove fields that don't need to be public
        del project_dict['keep']
        del project_dict['tsv_body']
        del project_dict['last_updated_issues']
        del project_dict['last_updated_civic_json']
        del project_dict['last_updated_root_files']

        project_dict['api_url'] = self.api_url()

        if include_organization:
            project_dict['organization'] = self.organization.asdict()

        if include_issues:
            project_dict['issues'] = [o.asdict() for o in db.session.query(Issue).filter(Issue.project_id == project_dict['id']).all()]

        return project_dict

tbl = Project.__table__
# Index the tsvector column
db.Index('index_project_tsv_body', tbl.c.tsv_body, postgresql_using='gin')

# Trigger to populate the search index column
trig_ddl = DDL("""
    CREATE TRIGGER tsvupdate_projects_trigger BEFORE INSERT OR UPDATE ON project FOR EACH ROW EXECUTE PROCEDURE tsvector_update_trigger(tsv_body, 'pg_catalog.english', name, description, type, categories, tags, github_details, status);
""")
# Initialize the trigger after table is created
event.listen(tbl, 'after_create', trig_ddl.execute_if(dialect='postgresql'))
