from math import ceil
from flask import request
from urllib import urlencode

def page_info(query, page, limit):
    ''' Return last page and offset for a query.
    '''
    # Get a bunch of projects.
    total = query.count()
    last = int(ceil(total / float(limit)))
    offset = (page - 1) * limit

    return last, offset

def pages_dict(page, last, querystring):
    ''' Return a dictionary of pages to return in API responses.
    '''
    url = '%s://%s%s' % (request.scheme, request.host, request.path)

    pages = dict()

    if page > 1:
        pages['first'] = dict()
        pages['prev'] = dict()
        if 'per_page' in request.args:
            pages['first']['per_page'] = request.args['per_page']
            pages['prev']['per_page'] = request.args['per_page']

    if page > 2:
        pages['prev']['page'] = page - 1

    if page < last:
        pages['next'] = {'page': page + 1}
        pages['last'] = {'page': last}
        if 'per_page' in request.args:
            pages['next']['per_page'] = request.args['per_page']
            pages['last']['per_page'] = request.args['per_page']

    for key in pages:
        if querystring != '':
            pages[key] = '%s?%s&%s' % (url, urlencode(pages[key]), querystring) if pages[key] else url
        else:
            pages[key] = '%s?%s' % (url, urlencode(pages[key])) if pages[key] else url

    return pages

def paged_results(query, page, per_page, querystring=''):
    '''
    '''
    total = query.count()
    last, offset = page_info(query, page, per_page)
    if(querystring.find("only_ids") != -1):
        model_dicts = [o.id for o in query.limit(per_page).offset(offset)]
    else:
        model_dicts = []
        for o in query.limit(per_page).offset(offset):
            obj = o.asdict(True)
            model_dicts.append(obj)
    return dict(total=total, pages=pages_dict(page, last, querystring), objects=model_dicts)

def get_query_params(args):
    filters = {}
    for key, value in args.iteritems():
        if 'page' not in key:
            filters[key] = value
    return filters, urlencode(filters)