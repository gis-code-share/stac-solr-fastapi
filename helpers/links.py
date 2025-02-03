from pystac import Link, RelType
from fastapi import Request
import json
from .models import LinkParameters
from helpers import param_utils
import logging
logging.basicConfig(filename='logs/stacapi.log', format='%(asctime)s %(message)s', datefmt='%m/%d/%Y %I:%M %p', level=logging.INFO)

with open(".\\configuration\\conf_local.json") as f:
    config = json.load(f)

defaultLimit = config["default_limit"]
linksHTTPSMode = config["linksHTTPSMode"]

def _get_self_link(p: LinkParameters):
    return Link(RelType.SELF, p.request.url._url)

def _get_root_link(p: LinkParameters):
    return Link(RelType.ROOT, p.request.base_url._url + config["api_root"][1:]) 

def _get_parent_link(p: LinkParameters):
    if '/' in p.request.url._url:
        url = "/".join(p.request.url._url.split('/')[:-1])
    return Link(RelType.PARENT, url)

def _get_alternate_link(p: LinkParameters):
    url = p.request.url._url.split('?')[0] if '?' in p.request.url._url else p.request.url._url
    if url.endswith('/search') or url.endswith('/collections') or url.endswith('/items'):
        url = p.request.base_url._url + config["api_root"][1:]
        
    url = url.replace(config["public_url_http"],  config["stac_browser_url"],)
    return Link(RelType.ALTERNATE, target=url, media_type="text/html", title="STAC BROWSER")

def _get_next_link(p: LinkParameters):
    if (p.start + p.numberReturned) < p.numberMatched and defaultLimit != 0:
        start_url, separator, end = prepare_url_parts(p.request)
        url = start_url + separator + str(p.start + p.numberReturned) + end
        return Link(RelType.NEXT, target=url, media_type= "application/geo+json")

def _get_previous_link(p: LinkParameters):
    if p.start >= p.numberReturned and p.numberReturned != 0:
        start_url, separator, end = prepare_url_parts(p.request)
        url = start_url + separator + str(p.start - p.limit) + end
        return Link(RelType.PREV, target=url, media_type= "application/geo+json")

_get_search_links_functions = [ _get_next_link, _get_previous_link]
_get_general_links_functions = [_get_self_link, _get_root_link, _get_parent_link, _get_alternate_link]

def add_links(result_object, parameters, function_list = _get_general_links_functions):
    parameters.limit = param_utils.check_if_value_is_valid(parameters.limit, "limit", config["default_limit"])
    parameters.start = param_utils.check_if_value_is_valid(parameters.start, "start", 0)
    
    if not "links" in result_object.keys():
        result_object["links"] = []
        
    for get_link in function_list:
        link = get_link(parameters)
        
        link = add_https(link)
        if link != None and link.rel not in get_existing_link_rels(result_object):
            result_object["links"].append(link.to_dict())
    return result_object

def add_search_links(result_object, request, start, numberMatched, numberReturned, limit):
    if limit == None: limit = defaultLimit
    linkParameters = LinkParameters(request, int(start), int(numberMatched), int(numberReturned), limit)
    result_object = add_links(result_object, linkParameters, _get_search_links_functions)
    return result_object

def add_general_links(result_object, request):
    result_object = add_links(result_object, LinkParameters(request = request), _get_general_links_functions)
    return result_object

def add_https(link):
    if link != None and "http:" in link.target and linksHTTPSMode == True:
        link.target = link.target.replace('http:', 'https:')
    return link

# change next link to get search
# input 'http://127.0.0.1:9063/search?&start=10'
# output 'http://127.0.0.1:9063/search?&start=10&collections=coll_ortho_villach&limit=10'
def add_query_params_to_post_response_links(result, params):
    if not isinstance(result, dict) or "links" not in result:
        return result
    for link in result["links"]:
        if link.get("rel") in {"next", "prev"}:
            href = link["href"]
            valid_params = {k: v for k, v in params.items() if v is not None} # Filter out None values from parameters

            if valid_params:
                param_str = "&".join(f"{k}={v}" for k, v in valid_params.items())
                link["href"] = f"{href}&{param_str}"  # Add parameters to href if there are any valid ones
    
    return result

def prepare_url_parts(request):
    url = request.url._url
    separator = "&start="
    if not '?' in url or "?&start=" in url:
        separator = "?" + str(separator)
        
    url_parts = url.split(separator)
    if len(url_parts) > 1 and '&' in url_parts[1]:
        end = '&' + '&'.join(url_parts[1].split('&')[1:])
    else: end = ""
    
    return str(url_parts[0]), separator, str(end) # returns start_url, separator, end

def get_existing_link_rels(result_object):
    rels = []
    for l in result_object["links"]:
        rels.append(l["rel"])
    return rels

