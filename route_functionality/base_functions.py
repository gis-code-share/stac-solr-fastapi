import json
from helpers import response_mapping, errorHandler, solr_helper
from starlette.exceptions import HTTPException
from pathlib import Path
import logging
logging.basicConfig(filename='logs/stacapi.log', format='%(asctime)s %(message)s', datefmt='%m/%d/%Y %I:%M %p', level=logging.INFO)

with open(".\\configuration\\conf.json") as f:
    config = json.load(f)

solr = config["solr_connection"]

def get_landing_page(request):
    """ Landing page of STAC catalog """
    try:
        response = solr_helper.get(solr + "/")

        if str(response.status_code).startswith('2'):
            result =  response_mapping.map_solr_to_api(response.json(), request.url.path, request.method.lower(), "200", request)
            result["conformsTo"] = config["conformsTo"]
            return result
        raise HTTPException(response.status_code, response.text)
    except HTTPException as ex:
        raise ex
    except Exception as ex:
        return errorHandler.errorResponse(None, None, ex, serverError=True)

def get_conformance():
    try:
        result = {"conformsTo": config["conformsTo"]}
        return result
    except Exception as ex:
        return errorHandler.errorResponse(None, None, ex, serverError=True)
    
def get_creation_logs():
    try:
        log_path = Path(config["creationLogFilePath"])
        if not log_path.exists():
            raise HTTPException(status_code=404, detail="Creation log file not found")
        
        response = {}
        with open(log_path, 'r', encoding='utf-8') as file:
            for line in file:
                if line and not json.loads(line): continue
                response = dict(response, **json.loads(line))
        return response
    except HTTPException as ex:
        raise ex
    except Exception as ex:
        return errorHandler.errorResponse(None, None, ex, serverError=True)