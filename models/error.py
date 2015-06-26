from . import db

class Error(db.Model):
    '''
        Errors from run_update.py
    '''
    # Columns
    id = db.Column(db.Integer(), primary_key=True)
    error = db.Column(db.Unicode())
    time = db.Column(db.DateTime(False))
