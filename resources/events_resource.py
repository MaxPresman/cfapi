from flask import Blueprint
from flask import request, jsonify
from sqlalchemy import desc
from utils.request_utils import get_query_params, paged_results
from models import db, Organization, Event
from datetime import datetime

blueprint = Blueprint('events_resource', __name__)

@blueprint.route('/api/events')
@blueprint.route('/api/events/<int:id>')
def get_events(id=None):
    ''' Regular response option for events.
    '''

    filters = request.args
    filters, querystring = get_query_params(request.args)

    if id:
        # Get one named event.
        filter = Event.id == id
        event = db.session.query(Event).filter(filter).first()
        if event:
            return jsonify(event.asdict(True))
        else:
            # If no event found
            return jsonify({"status": "Resource Not Found"}), 404

    # Get a bunch of events.
    query = db.session.query(Event)

    for attr, value in filters.iteritems():
        if 'organization' in attr:
            org_attr = attr.split('_')[1]
            query = query.join(Event.organization).filter(getattr(Organization, org_attr).ilike('%%%s%%' % value))
        else:
            query = query.filter(getattr(Event, attr).ilike('%%%s%%' % value))

    response = paged_results(query, int(request.args.get('page', 1)), int(request.args.get('per_page', 25)), querystring)
    return jsonify(response)

@blueprint.route('/api/events/upcoming_events')
def get_all_upcoming_events():
    ''' Show all upcoming events.
        Return them in chronological order.
    '''
    filters = request.args
    filters, querystring = get_query_params(request.args)

    query = db.session.query(Event).filter(Event.start_time_notz >= datetime.utcnow()).order_by(Event.start_time_notz)

    for attr, value in filters.iteritems():
        if 'organization' in attr:
            org_attr = attr.split('_')[1]
            query = query.join(Event.organization).filter(getattr(Organization, org_attr).ilike('%%%s%%' % value))
        else:
            query = query.filter(getattr(Event, attr).ilike('%%%s%%' % value))

    response = paged_results(query, int(request.args.get('page', 1)), int(request.args.get('per_page', 25)))
    return jsonify(response)


@blueprint.route('/api/events/past_events')
def get_all_past_events():
    ''' Show all past events.
        Return them in reverse chronological order.
    '''
    filters = request.args
    filters, querystring = get_query_params(request.args)

    query = db.session.query(Event).filter(Event.start_time_notz <= datetime.utcnow()).order_by(desc(Event.start_time_notz))

    for attr, value in filters.iteritems():
        if 'organization' in attr:
            org_attr = attr.split('_')[1]
            query = query.join(Event.organization).filter(getattr(Organization, org_attr).ilike('%%%s%%' % value))
        else:
            query = query.filter(getattr(Event, attr).ilike('%%%s%%' % value))

    response = paged_results(query, int(request.args.get('page', 1)), int(request.args.get('per_page', 25)))
    return jsonify(response)