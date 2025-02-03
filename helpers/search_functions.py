from fastapi import  Request
import json, requests
from helpers import param_utils, response_mapping, errorHandler, links, solr_helper
from starlette.exceptions import HTTPException
import logging
logging.basicConfig(filename='logs/stacapi.log', format='%(asctime)s %(message)s', datefmt='%m/%d/%Y %I:%M %p', level=logging.INFO)

with open(".\\configuration\\conf_local.json") as f:
    config = json.load(f)

solr = config["solr_connection"]

def get_search(solr_request, query_params, method, limit, start, sortby, sortdesc):
    solr_request += param_utils.get_filter_query_params(query_params, method)
    solr_request = param_utils.add_limit_and_start(solr_request, limit, start)
    solr_request = param_utils.add_sort(solr_request, sortby, sortdesc)
    return solr_helper.get(solr_request), solr_request

def post_search(solr_request, query_params, method, limit, sortby, sortdesc):
    if limit == None: limit = config["default_limit"]
    solr_request += "post"
    filter = param_utils.get_filter_query_params(query_params, method).replace('?&fq=', '').split(' AND ')
    sortby, sortdesc = param_utils.check_sort(sortby, sortdesc)
    
    body = {
        "filter": filter,
        "limit": limit
    }
    if sortby != None: body["sort"] = sortby + " " + sortdesc
    return solr_helper.post(solr_request, json.dumps(body), headers={"Content-Type": "application/json"}), solr_request
                                       

def search(request: Request, url, collection=None, bbox=None, datetime=None, ids = None, limit=None, start=0, sortby = None, sortdesc = 0):
    try:
        method = request.method.lower()
        solr_request = solr + "/search"
        query_params = {"collections": collection, "bbox": bbox, "datetime": datetime, "ids": ids}
        other_params = {"limit": limit, "sortby": sortby, "sortdesc": sortdesc}
        
        if method == "get":
            response, solr_request = get_search(solr_request, query_params, method, limit, start, sortby, sortdesc)
        elif method == "post":
            response, solr_request = post_search(solr_request, query_params, method, limit, sortby, sortdesc)

        if str(response.status_code).startswith('2'):
            if method == "get":
                numberMatched = response.json()["numFound"]
                result = response_mapping.map_solr_to_api(response.json(), url, method, "200", request)
                numberReturned = result["numberReturned"] if "numberReturned" in result.keys() else 1
                return links.add_search_links(result, request, start, numberMatched, numberReturned, limit)
            result = response_mapping.map_solr_to_api(response.json()["response"], url, method, "200", request)
            result = links.add_search_links(result, request, start, result["numberMatched"], result["numberReturned"], limit)
            response = links.add_query_params_to_post_response_links(result, {**query_params, **other_params})
            return response

        return errorHandler.errorResponse(response)
    except HTTPException as ex:
        raise ex
    except Exception as ex:
            return errorHandler.errorResponse(None, None, ex, serverError = True)

