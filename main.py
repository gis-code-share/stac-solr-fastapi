from fastapi import FastAPI, Request, responses
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import RedirectResponse
import yaml
from pathlib import Path
import uvicorn
import requests
from helpers import param_utils, solr_helper, models, links, errorHandler, response_mapping, search_functions
import json

from starlette.exceptions import HTTPException
from fastapi.staticfiles import StaticFiles
from starlette.responses import FileResponse
import logging
logging.basicConfig(filename='logs/stacapi.log', format='%(asctime)s %(message)s', datefmt='%m/%d/%Y %I:%M %p', level=logging.INFO)

with open(".\\configuration\\conf_local.json") as f:
    config = json.load(f)

port = config["port"]
solr = config["solr_connection"]
host = config["host"]
root = config["api_root"]

app = FastAPI(title= "STAC API",
    description = "description",
    version = "1.0.0",
    contact = config["apiContact"]
    )

app.add_middleware(
    CORSMiddleware,
    allow_origins = ["*"],
    allow_credentials = False,
    allow_methods = ["GET", "POST", "OPTIONS"],
    allow_headers = ["Content-Type"],
)

@app.exception_handler(HTTPException)
async def http_exception_handler(request, exc):
    return errorHandler.errorResponse(None, str(exc.status_code), str(exc.detail))

@app.middleware(middleware_type="http")
async def middleware_function(request: Request, call_next):
    response = await call_next(request)
    if response.status_code == 422:
        return errorHandler.errorResponse(None, str(422), "value of body attribute is invalid type")
    else: return response

@app.get(root, response_class=RedirectResponse, status_code=302, include_in_schema = False)
async def landing_page_root(request: Request):
    return config["public_url_https"]

@app.get(root + "/")
def landing_page(request: Request):
    """ Landing page of STAC catalog """
    try:
        response = solr_helper.get(solr + "/")

        if str(response.status_code).startswith('2'):
            result =  response_mapping.map_solr_to_api(response.json(), request.url.path, request.method.lower(), "200", request)
            result["conformsTo"] = config["conformsTo"]
            return result
        return errorHandler.errorResponse(response)
    except HTTPException as ex:
        raise ex
    except Exception as ex:
        return errorHandler.errorResponse(None, None, ex, serverError=True)

@app.get(root + "/conformance")
def conformance():
    try:
        result = {"conformsTo": config["conformsTo"]}
        return result
    except Exception as ex:
        return errorHandler.errorResponse(None, None, ex, serverError=True)

@app.get(root + "/search")
def search(request: Request, collections=None, bbox=None, datetime=None, ids=None, limit=None, start=0, sortby = None, sortdesc = 0):
    return search_functions.search(request, request.url.path, collections, bbox, datetime, ids, limit, start, sortby, sortdesc)

@app.post(root + "/search")
def search(request: Request, searchBody: models.SearchBody):
    bbox, collections, ids, sortby, sortdesc = param_utils.map_search_body(searchBody)
    return search_functions.search(request, request.url.path, collections, bbox, searchBody.datetime, ids, searchBody.limit, searchBody.start, sortby, sortdesc)


@app.get(root + "/collections")
def get_collections(request: Request, f = None, limit = None, start = 0):
    try:
        solr_request = solr + "/collections"
        solr_request = param_utils.add_limit_and_start(solr_request, limit, start, default_limit = 30)
        response = solr_helper.get(solr_request)

        if str(response.status_code).startswith('2'):
            numberMatched = response.json()["numFound"]
            result = response_mapping.map_solr_to_api(response.json(), request.url.path, request.method.lower(), "200", request)
            numberReturned = len(result["collections"])
            return links.add_search_links(result, request, start, numberMatched, numberReturned, limit)
        return errorHandler.errorResponse(response)

    except HTTPException as ex:
        raise ex
    except Exception as ex:
        return errorHandler.errorResponse(None, None, ex, serverError=True)

get_one_collection_url = root + "/collections/{collectionId}"
@app.get(get_one_collection_url)
def get_one_collection(request: Request, collectionId: str):
    try:
        response = solr_helper.get(solr + "/collections?fq=id:" + collectionId)

        if str(response.status_code).startswith('2'):
            return response_mapping.map_solr_to_api(response.json(), get_one_collection_url, request.method.lower(), "200", request)
        return errorHandler.errorResponse(response)
    except HTTPException as ex:
        raise ex
    except Exception as ex:
        return errorHandler.errorResponse(None, None, ex, serverError=True)

get_items_of_collection_url = root + "/collections/{collectionId}/items"
@app.get(get_items_of_collection_url)
def get_items_of_collection(request: Request, collectionId: str, bbox=None, datetime=None, ids = None, limit=None, start=0, sortby = None, sortdesc = 0):
    return search_functions.search(request, get_items_of_collection_url, collectionId, bbox, datetime, ids, limit, start, sortby, sortdesc)

get_one_item_url = root + "/collections/{collectionId}/items/{itemId}"
@app.get(get_one_item_url)
def get_one_item(request: Request, collectionId: str, itemId: str):
    return search_functions.search(request, get_one_item_url, collectionId, ids = itemId)



app.mount(root + "/api", StaticFiles(directory="openAPI"), name="openAPI")

@app.get(root + "/api")
def get_documentation_yaml(request: Request):
    """ Returns file response YAML of openAPI documentation. """
    return FileResponse("./openAPI/openapi.yaml", media_type='application/vnd.oai.openapi+yaml;version=3.0',filename="KAGIS_STAC_API.yaml")

@app.get(root + "/api.html", response_class=RedirectResponse, status_code=302)
async def redirect_documentation(request: Request):
    """ Redirects to self hosted swagger instance. """
    return config["self_hosted_swagger_url"]

@app.get(root + "/browser", response_class=RedirectResponse, status_code=302)
async def redirect_stac_browser(request: Request):
    """ Redirects to STAC Browser. """
    return config["stac_browser_url"]

@app.get(root + "/creation-logs", include_in_schema=False)
def get_logs(request: Request):
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

def run():
    uvicorn.run(app, port=port, host=host)

if __name__ == '__main__':
    run()