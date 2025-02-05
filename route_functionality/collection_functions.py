import json
from helpers import param_utils, response_mapping, errorHandler, links, solr_helper
from starlette.exceptions import HTTPException
import logging
logging.basicConfig(filename='logs/stacapi.log', format='%(asctime)s %(message)s', datefmt='%m/%d/%Y %I:%M %p', level=logging.INFO)

with open(".\\configuration\\conf.json") as f:
    config = json.load(f)

solr = config["solr_connection"]


def get_all_collections(request, limit, start):
    try:
        solr_request = solr + "/collections"
        solr_request = param_utils.add_limit_and_start(solr_request, limit, start, default_limit = 30)
        response = solr_helper.get(solr_request)

        if str(response.status_code).startswith('2'):
            numberMatched = response.json()["numFound"]
            result = response_mapping.map_solr_to_api(response.json(), request.url.path, request.method.lower(), "200", request)
            numberReturned = len(result["collections"])
            return links.add_search_links(result, request, start, numberMatched, numberReturned, limit)
        raise HTTPException(response.status_code, response.text)
    except HTTPException as ex:
        raise ex
    except Exception as ex:
        return errorHandler.errorResponse(None, None, ex, serverError=True)

def get_one_collection(request, collectionId, get_one_collection_url):
    try:
        response = solr_helper.get(solr + "/collections?fq=id:" + collectionId)
        if str(response.status_code).startswith('2'):
            return response_mapping.map_solr_to_api(response.json(), get_one_collection_url, request.method.lower(), "200", request)
        raise HTTPException(response.status_code, response.text)
    except HTTPException as ex:
        raise ex
    except Exception as ex:
        return errorHandler.errorResponse(None, None, ex, serverError=True)