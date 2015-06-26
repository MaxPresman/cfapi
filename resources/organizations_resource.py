from flask import Blueprint
from sqlalchemy import desc, func
from sqlalchemy.orm import defer
from utils.name_utils import raw_name
from flask import request, jsonify
from utils.request_utils import get_query_params, paged_results
from models import db, Organization, Event, Project, Issue, Story, Label
from datetime import datetime

blueprint = Blueprint('organizations_resource', __name__)

@blueprint.route('/api/organizations')
@blueprint.route('/api/organizations/<name>')
def get_organizations(name=None):
    ''' Regular response option for organizations.
    '''

    filters = request.args
    filters, querystring = get_query_params(request.args)

    if name:
        # Get one named organization.
        filter = Organization.name == raw_name(name)
        org = db.session.query(Organization).filter(filter).first()
        if org:
            return jsonify(org.asdict(True))
        else:
            # If no org found
            return jsonify({"status": "Resource Not Found"}), 404

    # Get a bunch of organizations.
    query = db.session.query(Organization)
    # Default ordering of results
    ordering = desc(Organization.last_updated)

    for attr, value in filters.iteritems():
        if 'q' in attr:
            query = query.filter("organization.tsv_body @@ plainto_tsquery('%s')" % value)
            ordering = desc(func.ts_rank(Organization.tsv_body, func.plainto_tsquery('%s' % value)))
        else:
            query = query.filter(getattr(Organization, attr).ilike('%%%s%%' % value))

    query = query.order_by(ordering)
    response = paged_results(query, int(request.args.get('page', 1)), int(request.args.get('per_page', 10)), querystring)

    return jsonify(response)

@blueprint.route('/api/organizations.geojson')
def get_organizations_geojson():
    ''' GeoJSON response option for organizations.
    '''
    geojson = dict(type='FeatureCollection', features=[])

    for org in db.session.query(Organization):
        # The unique identifier of an organization.
        id = org.api_id()

        # Pick out all the properties that aren't part of the location.
        props = org.asdict()

        # GeoJSON Point geometry, http://geojson.org/geojson-spec.html#point
        geom = dict(type='Point', coordinates=[org.longitude, org.latitude])

        feature = dict(type='Feature', id=id, properties=props, geometry=geom)
        geojson['features'].append(feature)

    return jsonify(geojson)

@blueprint.route("/api/organizations/<organization_name>/events")
def get_orgs_events(organization_name):
    '''
        A cleaner url for getting an organizations events
        Better than /api/events?q={"filters":[{"name":"organization_name","op":"eq","val":"Code for San Francisco"}]}
    '''
    # Check org name
    organization = Organization.query.filter_by(name=raw_name(organization_name)).first()
    if not organization:
        return "Organization not found", 404

    # Get event objects
    query = Event.query.filter_by(organization_name=organization.name)
    response = paged_results(query, int(request.args.get('page', 1)), int(request.args.get('per_page', 25)))
    return jsonify(response)

@blueprint.route("/api/organizations/<organization_name>/upcoming_events")
def get_upcoming_events(organization_name):
    '''
        Get events that occur in the future. Order asc.
    '''
    # Check org name
    organization = Organization.query.filter_by(name=raw_name(organization_name)).first()
    if not organization:
        return "Organization not found", 404
    # Get upcoming event objects
    query = Event.query.filter(Event.organization_name == organization.name, Event.start_time_notz >= datetime.utcnow())
    response = paged_results(query, int(request.args.get('page', 1)), int(request.args.get('per_page', 25)))
    return jsonify(response)

@blueprint.route("/api/organizations/<organization_name>/past_events")
def get_past_events(organization_name):
    '''
        Get events that occur in the past. Order desc.
    '''
    # Check org name
    organization = Organization.query.filter_by(name=raw_name(organization_name)).first()
    if not organization:
        return "Organization not found", 404
    # Get past event objects
    query = Event.query.filter(Event.organization_name == organization.name, Event.start_time_notz < datetime.utcnow()).\
        order_by(desc(Event.start_time_notz))
    response = paged_results(query, int(request.args.get('page', 1)), int(request.args.get('per_page', 25)))
    return jsonify(response)

@blueprint.route("/api/organizations/<organization_name>/stories")
def get_orgs_stories(organization_name):
    '''
        A cleaner url for getting an organizations stories
    '''
    # Check org name
    organization = Organization.query.filter_by(name=raw_name(organization_name)).first()
    if not organization:
        return "Organization not found", 404

    # Get story objects
    query = Story.query.filter_by(organization_name=organization.name).order_by(desc(Story.id))
    response = paged_results(query, int(request.args.get('page', 1)), int(request.args.get('per_page', 25)))
    return jsonify(response)

@blueprint.route("/api/organizations/<organization_name>/projects")
def get_orgs_projects(organization_name):
    '''
        A cleaner url for getting an organizations projects
    '''
    # Check org name
    organization = Organization.query.filter_by(name=raw_name(organization_name)).first()
    if not organization:
        return "Organization not found", 404

    filters, querystring = get_query_params(request.args)

    # Get project objects
    query = db.session.query(Project).filter_by(organization_name=organization.name).options(defer('tsv_body'))

    # Default ordering of results
    last_updated_ordering_filter = Project.last_updated
    relevance_ordering_filter = None
    ordering_filter_name = 'last_updated'
    ordering_filter = last_updated_ordering_filter
    ordering_dir = 'desc'
    ordering = None

    for attr, value in filters.iteritems():
        if 'q' in attr:
            # Returns all results if the value is empty
            if value:
                query = query.filter("project.tsv_body @@ plainto_tsquery('%s')" % value)
                relevance_ordering_filter = func.ts_rank(Project.tsv_body, func.plainto_tsquery('%s' % value))
                ordering_filter_name = 'relevance'
        elif 'only_ids' in attr:
            query = query.with_entities(Project.id)
        elif 'sort_by' in attr:
            if(value == 'relevance'):
                ordering_filter_name = 'relevance'
            else:
                ordering_filter_name = 'last_updated'
        elif 'sort_dir' in attr:
            if(value == 'asc'):
                ordering_dir = 'asc'
            else:
                ordering_dir = 'desc'
        else:
            query = query.filter(getattr(Project, attr).ilike('%%%s%%' % value))

    if(ordering_filter_name == 'last_updated'):
        ordering_filter = last_updated_ordering_filter
    elif(ordering_filter_name == 'relevance' and dir(relevance_ordering_filter) != dir(None)):
        ordering_filter = relevance_ordering_filter

    if(ordering_dir == 'desc'):
        ordering = ordering_filter.desc()
    else:
        ordering = ordering_filter.asc()
    query = query.order_by(ordering)

    response = paged_results(query, int(request.args.get('page', 1)), int(request.args.get('per_page', 10)), querystring)
    return jsonify(response)

@blueprint.route("/api/organizations/<organization_name>/issues")
@blueprint.route("/api/organizations/<organization_name>/issues/labels/<labels>")
def get_orgs_issues(organization_name, labels=None):
    ''' A clean url to get an organizations issues
    '''

    # Get one named organization.
    organization = Organization.query.filter_by(name=raw_name(organization_name)).first()
    if not organization:
        return "Organization not found", 404

    # Get that organization's projects
    projects = Project.query.filter_by(organization_name=organization.name).all()
    project_ids = [project.id for project in projects]

    if labels:
        # Get all issues belonging to these projects
        query = Issue.query.filter(Issue.project_id.in_(project_ids))

        # Create a labels list by comma separating the argument
        labels = [label.strip() for label in labels.split(',')]

        # Create the filter for each label
        labels = [Label.name.ilike('%%%s%%' % label) for label in labels]

        # Create the base query object by joining on Issue.labels
        query = query.join(Issue.labels)

        # Filter for issues with each individual label
        label_queries = [query.filter(L) for L in labels]

        # Intersect filters to find issues with all labels
        query = query.intersect(*label_queries).order_by(func.random())

    else:
        # Get all issues belonging to these projects
        query = Issue.query.filter(Issue.project_id.in_(project_ids)).order_by(func.random())

    response = paged_results(query, int(request.args.get('page', 1)), int(request.args.get('per_page', 10)))
    return jsonify(response)