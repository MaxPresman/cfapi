from flask_sqlalchemy import SQLAlchemy

db = SQLAlchemy()

# load up the models for easy access
from story import Story
from issue import Issue
from project import Project
from event import Event
from label import Label
from error import Error
from organization import Organization
