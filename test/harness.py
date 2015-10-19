import unittest
from models import db
from app import app


class IntegrationTest(unittest.TestCase):
    def setUp(self):
        # Set up the database settings
        # app.config['SQLALCHEMY_DATABASE_URI'] = 'postgres://postgres@localhost/civic_json_worker_test'
        app.config['SQLALCHEMY_DATABASE_URI'] = 'postgres:///civic_json_worker_test'
        db.app = app
        db.init_app(app)
        db.create_all()
        self.app = app.test_client()

    def tearDown(self):
        db.session.close()
        db.drop_all()
