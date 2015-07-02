from . import db
from sqlalchemy.orm import backref


class Label(db.Model):
    '''
        Issue labels for projects on Github
    '''
    # Columns
    id = db.Column(db.Integer(), primary_key=True)
    name = db.Column(db.Unicode())
    color = db.Column(db.Unicode())
    url = db.Column(db.Unicode())

    # Relationships
    # child
    issue = db.relationship('Issue', single_parent=True, cascade='all, delete-orphan', backref=backref("labels", cascade="save-update, delete"))
    issue_id = db.Column(db.Integer, db.ForeignKey('issue.id', ondelete='CASCADE'), nullable=False, index=True)

    def __init__(self, name, color, url, issue_id=None):
        self.name = name
        self.color = color
        self.url = url
        self.issue_id = issue_id

    def asdict(self):
        '''
            Return label as a dictionary with some properties tweaked
        '''
        label_dict = db.Model.asdict(self)

        # remove fields that don't need to be public
        del label_dict['id']
        del label_dict['issue_id']

        return label_dict
