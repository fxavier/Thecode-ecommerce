import graphene
from django.conf import settings
from django.core.paginator import EmptyPage, PageNotAnInteger, Paginator
import re
from django.db.models import Q


def is_authenticated(func):
    """
    Decorator to check if the user is authenticated.
    """
    def wrapper(cls, info, **kwargs):
        if not info.context.user:
            raise Exception(
                "You are not authorized to perform operations")

        return func(cls, info, **kwargs)

    return wrapper


def paginate(model_type):
    """
    Creates a paginated Graphene object type for the given model_type.
    """
    structure = {
        "total": graphene.Int(),
        "size": graphene.Int(),
        "current": graphene.Int(),
        "has_next": graphene.Boolean(),
        "has_prev": graphene.Boolean(),
        "results": graphene.List(model_type)
    }

    return type(f"{model_type}Paginated", (graphene.ObjectType,), structure)


def resolve_paginated(query_data, info, page_info):
    """
    Helper function to resolve paginated GraphQL queries.
    """
    def get_paginated_data(qs, paginated_type, page):
        page_size = settings.GRAPHENE.get("PAGE_SIZE", 10)

        try:
            qs.count()
        except Exception as e:
            raise ValueError(f"Error counting queryset: {e}")

        paginator = Paginator(qs, page_size)

        try:
            page_obj = paginator.page(page)
        except PageNotAnInteger:
            page_obj = paginator.page(1)
        except EmptyPage:
            page_obj = paginator.page(paginator.num_pages)

        result = paginated_type.graphene_type(
            total=paginator.num_pages,
            size=qs.count(),
            current=page_obj.number,
            has_next=page_obj.has_next(),
            has_prev=page_obj.has_previous(),
            results=page_obj.object_list
        )

        return result

    return get_paginated_data(query_data, info.return_type, page_info)


def normalize_query(
        query_string, findterms=re.compile(r'"([^"]+)"|(\S+)')
        .findall, normspace=re.compile(r'\s{2,}').sub):
    """
    Normalizes a query string by splitting it into a list of terms.
    """
    return [normspace(
        ' ', (t[0] or t[1]).strip()) for t in findterms(query_string)]


def get_query(query_string, search_fields):
    """
    Creates a combined Django Q object for search queries 
    based on the search string and specified fields.
    """
    combined_query = None
    terms = normalize_query(query_string)
    for term in terms:
        or_query = None
        for field_name in search_fields:
            q = Q(**{"%s__icontains" % field_name: term})
            if or_query is None:
                or_query = q
            else:
                or_query = or_query | q
        if combined_query is None:
            combined_query = or_query
        else:
            combined_query = combined_query & or_query
    return combined_query
