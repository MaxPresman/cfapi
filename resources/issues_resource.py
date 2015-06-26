from flask import Blueprint
from sqlalchemy import func
from flask import request, jsonify
from utils.request_utils import get_query_params, paged_results
from models import db, Organization, Project, Issue, Label

blueprint = Blueprint('issues_resource', __name__)

@blueprint.route('/api/issues')
@blueprint.route('/api/issues/<int:id>')
def get_issues(id=None):
    '''Regular response option for issues.
    '''

    filters = request.args
    filters, querystring = get_query_params(request.args)

    if id:
        # Get one issue
        filter = Issue.id == id
        issue = db.session.query(Issue).filter(filter).first()
        if issue:
            return jsonify(issue.asdict(True))
        else:
            # If no issue found
            return jsonify({"status": "Resource Not Found"}), 404

    # Get a bunch of issues
    query = db.session.query(Issue).order_by(func.random())

    for attr, value in filters.iteritems():
        if 'project' in attr:
            proj_attr = attr.split('_')[1]
            query = query.join(Issue.project).filter(getattr(Project, proj_attr).ilike('%%%s%%' % value))
        elif 'organization' in attr:
            org_attr = attr.split('_')[1]
            query = query.join(Issue.project).join(Project.organization).filter(getattr(Organization, org_attr).ilike('%%%s%%' % value))
        else:
            query = query.filter(getattr(Issue, attr).ilike('%%%s%%' % value))

    response = paged_results(query, int(request.args.get('page', 1)), int(request.args.get('per_page', 10)), querystring)
    return jsonify(response)

@blueprint.route('/api/issues/labels/<labels>')
def get_issues_by_labels(labels):
    '''
    A clean url to filter issues by a comma-separated list of labels
    '''

    # Create a labels list by comma separating the argument
    labels = [label.strip() for label in labels.split(',')]

    # Create the filter for each label
    labels = [Label.name.ilike('%%%s%%' % label) for label in labels]

    # Create the base query object by joining on Issue.labels
    base_query = db.session.query(Issue).join(Issue.labels)

    # Check for parameters
    filters = request.args
    filters, querystring = get_query_params(request.args)
    for attr, value in filters.iteritems():
        if 'project' in attr:
            proj_attr = attr.split('_')[1]
            base_query = base_query.join(Issue.project).filter(getattr(Project, proj_attr).ilike('%%%s%%' % value))
        elif 'organization' in attr:
            org_attr = attr.split('_')[1]
            base_query = base_query.join(Issue.project).join(Project.organization).filter(getattr(Organization, org_attr).ilike('%%%s%%' % value))
        else:
            base_query = base_query.filter(getattr(Issue, attr).ilike('%%%s%%' % value))

    # Filter for issues with each individual label
    label_queries = [base_query.filter(L) for L in labels]

    # Intersect filters to find issues with all labels
    query = base_query.intersect(*label_queries).order_by(func.random())

    # Return the paginated reponse
    response = paged_results(query, int(request.args.get('page', 1)), int(request.args.get('per_page', 10)))
    return jsonify(response)