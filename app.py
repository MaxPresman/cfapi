# -------------------
# Imports
# -------------------

from __future__ import division

from datetime import date
import os
import time
from mimetypes import guess_type
from os.path import join

from flask import Flask, make_response, request, jsonify, render_template
import requests
from flask.ext.heroku import Heroku
from sqlalchemy import desc
from dictalchemy import make_class_dictable
from flask.ext.script import Manager, prompt_bool
from flask.ext.migrate import Migrate, MigrateCommand
from werkzeug.contrib.fixers import ProxyFix

from models import db, Project, Organization, Error
from utils.response_utils import add_cors_header

# -------------------
# Init
# -------------------

app = Flask(__name__)
heroku = Heroku(app)

db.app = app
db.init_app(app)

migrate = Migrate(app, db)
manager = Manager(app)
manager.add_command('db', MigrateCommand)

# -------------------
# Register blueprints
# -------------------
from resources import events_resource, issues_resource, organizations_resource, \
    projects_resource, stories_resource

app.register_blueprint(organizations_resource.blueprint)
app.register_blueprint(issues_resource.blueprint)
app.register_blueprint(events_resource.blueprint)
app.register_blueprint(projects_resource.blueprint)
app.register_blueprint(stories_resource.blueprint)


make_class_dictable(db.Model)

app.wsgi_app = ProxyFix(app.wsgi_app)
app.after_request(add_cors_header)

# -------------------
# hook-up commands for CLI
# -------------------

@manager.command
def dropdb():
    if prompt_bool("Are you sure you want to lose all your data?"):
        db.drop_all()

@manager.command
def createdb():
    db.create_all()

# -------------------
# Routes
# -------------------
@app.route("/")
def index():
    response = make_response('Look in /api', 302)
    response.headers['Location'] = '/api'
    return response

@app.route("/api")
@app.route("/api/")
def api_index():
    try:
        print "-> %s: %s" % ('request.base_url', request.base_url)
        print "-> %s: %s" % ('request.environ', request.environ)
        print "-> %s: %s" % ('request.headers', request.headers)
        print "-> %s: %s" % ('request.host_url', request.host_url)
        print "-> %s: %s" % ('request.is_secure', request.is_secure)
        print "-> %s: %s" % ('request.scheme', request.scheme)
        print "-> %s: %s" % ('request.url', request.url)
        print "-> %s: %s" % ('request.url_root', request.url_root)
    except:
        pass

    return render_template('index.html', api_base='%s://%s' % (request.scheme, request.host))

@app.route("/api/static/<path:path>")
def api_static_file(path):
    local_path = join('static', path)
    mime_type, _ = guess_type(path)
    response = make_response(open(local_path).read())
    response.headers['Content-Type'] = mime_type
    return response

@app.errorhandler(404)
def page_not_found(error):
    return jsonify({"status": "Resource Not Found"}), 404

@app.errorhandler(500)
def internal_error(error):
    return jsonify({"status": "Resource Not Found"}), 500

if __name__ == "__main__":
    manager.run()
