from pystac import Link, RelType
from fastapi import Request
import json
from helpers import param_utils
import logging
logging.basicConfig(filename='logs/stacapi.log', format='%(asctime)s %(message)s', datefmt='%m/%d/%Y %I:%M %p', level=logging.INFO)

with open(".\\configuration\\conf_local.json") as f:
    config = json.load(f)

limit = config["default_limit"]


def _get_self_link(request: Request, start, numberMatched, numberReturned, limit):
    return Link(RelType.SELF, request.url._url)


def _get_root_link(request: Request, start, numberMatched, numberReturned, limit):
    return Link(RelType.ROOT, request.base_url._url + config["api_root"][1:]) 


def _get_parent_link(request: Request, start, numberMatched, numberReturned, limit):
    if '/' in request.url._url:
        url = "/".join(request.url._url.split('/')[:-1])
    return Link(RelType.PARENT, url)


def _get_alternate_link(request: Request, start, numberMatched, numberReturned, limit):
    url = request.url._url.split('?')[0] if '?' in request.url._url else request.url._url
    if url.endswith('/search') or url.endswith('/collections') or url.endswith('/items'):
        url = request.base_url._url + config["api_root"][1:]
    url = url.replace(
        config["public_url_http"],  config["stac_browser_url"],)
    return Link(RelType.ALTERNATE, target=url, media_type="text/html", title="STAC BROWSER")




def _get_next_link(request: Request, start, numberMatched, numberReturned, limit):
    if (start + numberReturned) < numberMatched and limit != 0:
        start_url, separator, end = prepare_url_parts(request)
        url = start_url + separator + str(start + numberReturned) + end
        return Link(RelType.NEXT, target=url, media_type= "application/geo+json")


def _get_previous_link(request: Request, start, numberMatched, numberReturned, limit):
    if start >= numberReturned and numberReturned != 0:
        start_url, separator, end = prepare_url_parts(request)
        url = start_url + separator + str(start-limit) + end
        return Link(RelType.PREV, target=url, media_type= "application/geo+json")


_get_search_links_functions = [ _get_next_link, _get_previous_link]
_get_general_links_functions = [_get_self_link, _get_root_link, _get_parent_link, _get_alternate_link]


def get_existing_link_rels(result_object):
    rels = []
    for l in result_object["links"]:
        rels.append(l["rel"])
    return rels
        

def add_links(result_object, request = None, start = None, numberMatched = None, numberReturned = None, limit = None, function_list = _get_general_links_functions):
    limit = param_utils.check_if_value_is_valid(limit, "limit", config["default_limit"])
    start = param_utils.check_if_value_is_valid(start, "start", 0)
    if not "links" in result_object.keys():
        result_object["links"] = []
    for get_link in function_list:
        link = get_link(request, int(start), numberMatched,
                        numberReturned, int(limit))
        if link != None and "http:" in link.target: link.target = link.target.replace('http:', 'https:')
        if link != None and link.rel not in get_existing_link_rels(result_object):
            result_object["links"].append(link.to_dict())
    return result_object

def add_search_links(result_object, request, start, numberMatched, numberReturned, limit):
    result_object = add_links(result_object, request, start, numberMatched, numberReturned, limit, _get_search_links_functions)
    return result_object

def add_general_links(result_object, request):
    result_object = add_links(result_object, request)
    return result_object

# change next link to get search
# input 'http://127.0.0.1:9063/search?&start=10'
# output 'http://127.0.0.1:9063/search?&start=10&collections=coll_ortho_villach&limit=10'
def add_query_params_to_post_response_links(result, params):
    for i in range(len(result["links"])):
        if result["links"][i]["rel"] == "next" or result["links"][i]["rel"] == "prev":
            link = result["links"][i]["href"]
            for p in params.keys():
                if params[p] != None:
                    link += f"&{p}={params[p]}"
            result["links"][i]["href"] = link
    return result

def prepare_url_parts(request):
    separator = "&start="
    if not '?' in request.url._url or "?&start=" in request.url._url:
        separator = "?" + separator
    url_parts = request.url._url.split(separator)
    if len(url_parts) > 1 and '&' in url_parts[1]:
        end = '&' + '&'.join(url_parts[1].split('&')[1:])
    else: end = ""
    return str(url_parts[0]), separator, str(end)

    
