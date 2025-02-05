import json
from helpers import param_utils, response_mapping, errorHandler, links, solr_helper
from starlette.exceptions import HTTPException
from helpers.models import SearchParameters
import logging
logging.basicConfig(filename='logs/stacapi.log', format='%(asctime)s %(message)s', datefmt='%m/%d/%Y %I:%M %p', level=logging.INFO)

with open(".\\configuration\\conf.json") as f:
    config = json.load(f)

solr = config["solr_connection"]

def get_search(solr_request, query_params, url, method, sp: SearchParameters):
    solr_request += param_utils.get_filter_query_params(query_params, method)
    solr_request = param_utils.add_limit_and_start(solr_request, sp.limit, sp.start)
    solr_request = param_utils.add_sort(solr_request, sp.sortby, sp.sortdesc)
    response = solr_helper.get(solr_request)
    
    if str(response.status_code).startswith('2'):
        numberMatched = response.json()["numFound"]
        result = response_mapping.map_solr_to_api(response.json(), url, method, "200", sp.request)
        numberReturned = result["numberReturned"] if "numberReturned" in result.keys() else 1
        return links.add_search_links(result, sp.request, sp.start, numberMatched, numberReturned, sp.limit)
    return errorHandler.errorResponse(response) 

def post_search(solr_request, query_params, other_params, url, method, sp: SearchParameters):
    if sp.limit == None: sp.limit = config["default_limit"]
    solr_request += "post"
    filter = param_utils.get_filter_query_params(query_params, method).replace('?&fq=', '').split(' AND ')
    sortby, sortdesc = param_utils.check_sort(sp.sortby, sp.sortdesc)
    
    body = {
        "filter": filter,
        "limit": sp.limit
    }
    if sortby != None: body["sort"] = sortby + " " + sortdesc
    response = solr_helper.post(solr_request, json.dumps(body), headers={"Content-Type": "application/json"})
    
    if str(response.status_code).startswith('2'):
        result = response_mapping.map_solr_to_api(response.json()["response"], url, method, "200", sp.request)
        result = links.add_search_links(result, sp.request, sp.start, result["numberMatched"], result["numberReturned"], sp.limit)
        response = links.add_query_params_to_post_response_links(result, {**query_params, **other_params})
        return response
    return errorHandler.errorResponse(response)      

def search(sp: SearchParameters, url = None):
    try:
        if url == None: url = sp.request.url.path
        method = sp.request.method.lower()
        solr_request = solr + "/search"
        query_params = {"collections": sp.collections, "bbox": sp.bbox, "datetime": sp.datetime, "ids": sp.ids}
        other_params = {"limit": sp.limit, "sortby": sp.sortby, "sortdesc": sp.sortdesc}
        
        if method == "get":
            return get_search(solr_request, query_params, url, method, sp)
        elif method == "post":
            return post_search(solr_request, query_params, other_params, url, method, sp)
        else:
            raise Exception("Unknown search method")
    except HTTPException as ex:
        raise ex
    except Exception as ex:
        return errorHandler.errorResponse(None, None, ex, serverError = True)

