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
from resources import events_resource, issues_resource, organizations_resource, projects_resource, stories_resource

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

@app.route('/api/.well-known/status')
def well_known_status():
    ''' Return status information for Engine Light.

        http://engine-light.codeforamerica.org
    '''
    if 'GITHUB_TOKEN' in os.environ:
        github_auth = (os.environ['GITHUB_TOKEN'], '')
    else:
        github_auth = None

    if 'MEETUP_KEY' in os.environ:
        meetup_key = os.environ['MEETUP_KEY']
    else:
        meetup_key = None

    try:
        org = db.session.query(Organization).order_by(Organization.last_updated).limit(1).first()
        project = db.session.query(Project).limit(1).first()
        rate_limit = requests.get('https://api.github.com/rate_limit', auth=github_auth)
        remaining_github = rate_limit.json()['resources']['core']['remaining']
        recent_error = db.session.query(Error).order_by(desc(Error.time)).limit(1).first()

        meetup_status = "No Meetup key set"
        if meetup_key:
            meetup_url = 'https://api.meetup.com/status?format=json&key=' + meetup_key
            meetup_status = requests.get(meetup_url).json().get('status')

        time_since_updated = time.time() - getattr(org, 'last_updated', -1)

        if not hasattr(project, 'name'):
            status = 'Sample project is missing a name'

        elif not hasattr(org, 'name'):
            status = 'Sample project is missing a name'

        elif recent_error:
            if recent_error.time.date() == date.today():
                status = recent_error.error
            else:
                status = 'ok' # is this really okay?

        elif time_since_updated > 16 * 60 * 60:
            status = 'Oldest organization (%s) updated more than 16 hours ago' % org.name

        elif remaining_github < 1000:
            status = 'Only %d remaining Github requests' % remaining_github

        elif meetup_status != 'ok':
            status = 'Meetup status is "%s"' % meetup_status

        else:
            status = 'ok'

    except Exception, e:
        status = 'Error: ' + str(e)

    state = dict(status=status, updated=int(time.time()), resources=[])
    state.update(dict(dependencies=['Meetup', 'Github', 'PostgreSQL']))

    return jsonify(state)

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
