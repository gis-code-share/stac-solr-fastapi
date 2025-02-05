from fastapi import FastAPI, Request
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import RedirectResponse
from helpers import param_utils, models, errorHandler
from route_functionality import base_functions, collection_functions, search_functions
import uvicorn
import json

from starlette.exceptions import HTTPException
from fastapi.staticfiles import StaticFiles
from starlette.responses import FileResponse
import logging

logging.basicConfig(filename='logs/stacapi.log', format='%(asctime)s %(message)s', datefmt='%m/%d/%Y %I:%M %p', level=logging.INFO)

with open(".\\configuration\\conf_test.json") as f:
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
    return base_functions.get_landing_page(request)

@app.get(root + "/conformance")
def conformance():
    return base_functions.get_conformance()

@app.get(root + "/search")
def search(request: Request, collections=None, bbox=None, datetime=None, ids=None, limit=None, start=0, sortby = None, sortdesc = 0):
    sp = models.SearchParameters(request, bbox, datetime, collections, limit, ids, sortby, sortdesc, start)
    return search_functions.search(sp)

@app.post(root + "/search")
def search(request: Request, searchBody: models.SearchBody):
    sp = param_utils.map_search_body(searchBody)
    sp.request = request
    return search_functions.search(sp)

@app.get(root + "/collections")
def get_collections(request: Request, f = None, limit = None, start = 0):
    return collection_functions.get_all_collections(request, limit, start)

get_one_collection_url = root + "/collections/{collectionId}"
@app.get(get_one_collection_url)
def get_one_collection(request: Request, collectionId: str):
    return collection_functions.get_one_collection(request, collectionId, get_one_collection_url)

get_items_of_collection_url = root + "/collections/{collectionId}/items"
@app.get(get_items_of_collection_url)
def get_items_of_collection(request: Request, collectionId: str, bbox=None, datetime=None, ids = None, limit=None, start=0, sortby = None, sortdesc = 0):
    sp = models.SearchParameters(request, bbox, datetime, collectionId, limit, ids, sortby, sortdesc, start)
    return search_functions.search(sp, get_items_of_collection_url)

get_one_item_url = root + "/collections/{collectionId}/items/{itemId}"
@app.get(get_one_item_url)
def get_one_item(request: Request, collectionId: str, itemId: str):
    sp = models.SearchParameters()
    sp.initCollsAndIds(request, collectionId, itemId)
    return search_functions.search(sp, get_one_item_url)

app.mount(root + "/api", StaticFiles(directory="openAPI"), name="openAPI")

@app.get(root + "/api")
def get_documentation_yaml(request: Request):
    """ Returns file response YAML of openAPI documentation. """
    return FileResponse("./openAPI/openapi.yaml", media_type='application/vnd.oai.openapi+yaml;version=3.0',filename="KAGIS_STAC_API.yaml")

@app.get(root + "/api.html", response_class=RedirectResponse, status_code=302)
async def redirect_documentation():
    """ Redirects to self hosted swagger instance. """
    return config["self_hosted_swagger_url"]

@app.get(root + "/browser", response_class=RedirectResponse, status_code=302)
async def redirect_stac_browser():
    """ Redirects to STAC Browser. """
    return config["stac_browser_url"]

@app.get(root + "/creation-logs", include_in_schema=False)
def get_logs():
    return base_functions.get_creation_logs()

def run():
    uvicorn.run(app, port=port, host=host)

if __name__ == '__main__':
    run()