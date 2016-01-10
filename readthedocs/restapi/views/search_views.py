import logging

from rest_framework import decorators, permissions, status
from rest_framework.renderers import JSONRenderer
from rest_framework.response import Response

from readthedocs.builds.constants import LATEST
from readthedocs.builds.models import Version
from readthedocs.search.indexes import PageIndex, ProjectIndex, SectionIndex
from readthedocs.restapi import utils


log = logging.getLogger(__name__)


@decorators.api_view(['POST'])
@decorators.permission_classes((permissions.IsAdminUser,))
@decorators.renderer_classes((JSONRenderer,))
def index_search(request):
    """
    Add things to the search index.
    """
    data = request.DATA['data']
    version_pk = data['version_pk']
    commit = data.get('commit')
    version = Version.objects.get(pk=version_pk)

    project_scale = 1
    page_scale = 1

    utils.index_search_request(
        version=version, page_list=data['page_list'], commit=commit,
        project_scale=project_scale, page_scale=page_scale)

    return Response({'indexed': True})


@decorators.api_view(['GET'])
@decorators.permission_classes((permissions.AllowAny,))
@decorators.renderer_classes((JSONRenderer,))
def search(request):
    project_slug = request.GET.get('project', None)
    version_slug = request.GET.get('version', LATEST)
    query = request.GET.get('q', None)
    if project_slug is None or query is None:
        return Response({'error': 'Need project and q'}, status=status.HTTP_400_BAD_REQUEST)
    log.debug("(API Search) %s" % query)

    kwargs = {}
    body = {
        "query": {
            "function_score": {
                "field_value_factor": {"field": "weight"},
                "query": {
                    "bool": {
                        "should": [
                            {"match": {
                                "title": {"query": query, "boost": 10}}},
                            {"match": {
                                "headers": {"query": query, "boost": 5}}},
                            {"match": {"content": {"query": query}}},
                        ]
                    }
                }
            }
        },
        "highlight": {
            "fields": {
                "title": {},
                "headers": {},
                "content": {},
            }
        },
        "fields": ["title", "project", "version", "path"],
        "size": 50  # TODO: Support pagination.
    }

    if project_slug:
        body['filter'] = {
            "and": [
                {"term": {"project": project_slug}},
                {"term": {"version": version_slug}},
            ]
        }
        # Add routing to optimize search by hitting the right shard.
        kwargs['routing'] = project_slug

    results = PageIndex().search(body, **kwargs)

    return Response({'results': results})


@decorators.api_view(['GET'])
@decorators.permission_classes((permissions.AllowAny,))
@decorators.renderer_classes((JSONRenderer,))
def project_search(request):
    query = request.GET.get('q', None)
    if query is None:
        return Response({'error': 'Need project and q'}, status=status.HTTP_400_BAD_REQUEST)

    log.debug("(API Project Search) %s" % (query))
    body = {
        "query": {
            "function_score": {
                "field_value_factor": {"field": "weight"},
                "query": {
                    "bool": {
                        "should": [
                            {"match": {"name": {"query": query, "boost": 10}}},
                            {"match": {"description": {"query": query}}},
                        ]
                    }
                }
            }
        },
        "fields": ["name", "slug", "description", "lang"]
    }
    results = ProjectIndex().search(body)

    return Response({'results': results})


@decorators.api_view(['GET'])
@decorators.permission_classes((permissions.AllowAny,))
@decorators.renderer_classes((JSONRenderer,))
def section_search(request):
    """
    Search for a Section of content on Read the Docs.
    A Section is a subheading on a specific page.

    Query Thoughts
    --------------

    If you want to search across all documents, just query with a ``q`` GET arg.
    If you want to filter by a specific project, include a ``project`` GET arg.

    Facets
    ------

    When you search, you will have a ``project`` facet, which includes the
    number of matching sections per project. When you search inside a project,
    the ``path`` facet will show the number of matching sections per page.

    Possible GET args
    -----------------

    * q - The query string **Required**
    * project - A project slug *Optional*
    * version - A version slug *Optional*
    * path - A file path slug  *Optional*

    Example
    -------

        GET /api/v2/search/section/?q=virtualenv&project=django

    Current Query
    -------------

    """
    query = request.GET.get('q', None)
    if not query:
        return Response(
            {'error': 'Search term required. Use the "q" GET arg to search. '},
            status=status.HTTP_400_BAD_REQUEST)

    project_slug = request.GET.get('project', None)
    version_slug = request.GET.get('version', LATEST)
    path_slug = request.GET.get('path', None)

    log.debug("(API Section Search) [%s:%s] %s" %
              (project_slug, version_slug, query))

    kwargs = {}
    body = {
        "query": {
            "function_score": {
                "field_value_factor": {"field": "weight"},
                "query": {
                    "bool": {
                        "should": [
                            {"match": {
                                "title": {"query": query, "boost": 10}}},
                            {"match": {"content": {"query": query}}},
                        ]
                    }
                }
            }
        },
        "facets": {
            "project": {
                "terms": {"field": "project"},
                "facet_filter": {
                    "term": {"version": version_slug},
                }
            },
        },
        "highlight": {
            "fields": {
                "title": {},
                "content": {},
            }
        },
        "fields": ["title", "project", "version", "path", "page_id", "content"],
        "size": 10  # TODO: Support pagination.
    }

    if project_slug:
        body['filter'] = {
            "and": [
                {"term": {"project": project_slug}},
                {"term": {"version": version_slug}},
            ]
        }
        body['facets']['path'] = {
            "terms": {"field": "path"},
            "facet_filter": {
                "term": {"project": project_slug},
            }
        },
        # Add routing to optimize search by hitting the right shard.
        kwargs['routing'] = project_slug

    if path_slug:
        body['filter'] = {
            "and": [
                {"term": {"path": path_slug}},
            ]
        }

    if path_slug and not project_slug:
        # Show facets when we only have a path
        body['facets']['path'] = {
            "terms": {"field": "path"}
        }

    results = SectionIndex().search(body, **kwargs)

    return Response({'results': results})
