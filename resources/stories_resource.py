from flask import Blueprint
from flask import request, jsonify
from sqlalchemy import desc
from utils.request_utils import get_query_params, paged_results
from models import db, Organization, Story

blueprint = Blueprint('stories_resource', __name__)

@blueprint.route('/api/stories')
@blueprint.route('/api/stories/<int:id>')
def get_stories(id=None):
    ''' Regular response option for stories.
    '''

    filters = request.args
    filters, querystring = get_query_params(request.args)

    if id:
        # Get one named story.
        filter = Story.id == id
        story = db.session.query(Story).filter(filter).first()
        if story:
            return jsonify(story.asdict(True))
        else:
            # If no story found
            return jsonify({"status": "Resource Not Found"}), 404

    # Get a bunch of stories.
    query = db.session.query(Story).order_by(desc(Story.id))

    for attr, value in filters.iteritems():
        if 'organization' in attr:
            org_attr = attr.split('_')[1]
            query = query.join(Story.organization).filter(getattr(Organization, org_attr).ilike('%%%s%%' % value))
        else:
            query = query.filter(getattr(Story, attr).ilike('%%%s%%' % value))

    response = paged_results(query, int(request.args.get('page', 1)), int(request.args.get('per_page', 25)), querystring)
    return jsonify(response)