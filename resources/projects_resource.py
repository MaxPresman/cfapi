from flask import Blueprint
from flask import request, jsonify
from sqlalchemy import func
from sqlalchemy.orm import defer
from utils.request_utils import get_query_params, paged_results
from models import db, Organization, Project

blueprint = Blueprint('projects_resource', __name__)

@blueprint.route('/api/projects')
@blueprint.route('/api/projects/<int:id>')
def get_projects(id=None):
    ''' Regular response option for projects.
    '''

    filters, querystring = get_query_params(request.args)

    if id:
        # Get one named project.
        filter = Project.id == id
        proj = db.session.query(Project).filter(filter).first()
        if proj:
            return jsonify(proj.asdict(True))
        else:
            # If no project found
            return jsonify({"status": "Resource Not Found"}), 404

    # Get a bunch of projects.
    query = db.session.query(Project).options(defer('tsv_body'))
    # Default ordering of results
    last_updated_ordering_filter = Project.last_updated
    relevance_ordering_filter = None
    ordering_filter_name = 'last_updated'
    ordering_filter = last_updated_ordering_filter
    ordering_dir = 'desc'
    ordering = None

    for attr, value in filters.iteritems():
        if 'organization' in attr:
            org_attr = attr.split('_')[1]
            query = query.join(Project.organization).filter(getattr(Organization, org_attr).ilike('%%%s%%' % value))
        elif 'q' in attr:
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