from starlette.exceptions import HTTPException
from datetime import datetime
import json
import re
from ciso8601 import parse_datetime

with open(".\\configuration\\conf_local.json") as f:
    config = json.load(f)
import logging
logging.basicConfig(filename='logs/stacapi.log', format='%(asctime)s %(message)s', datefmt='%m/%d/%Y %I:%M %p', level=logging.INFO)

def escape_user_input(user_input):
    # return special characters to avoid Solr Injection
    r =  re.sub(r"([\\+!%&(){}\[\]^\"~*?\|])", r"\\\1", user_input)
    return r.replace(" ", "")

def check_sort(sortby, sortdesc):
    #error: hello
    if sortby != None:
        if "-" in sortby:
            sortdesc = 1
            sortby = sortby.replace("-", "")
        sortby = sortby.replace("properties.", "")

    if sortby == "title": sortby = "id"

    if sortby not in [None, "collection", "datetime", "id"]:
        raise HTTPException(400, "sortby invalid value (collection, datetime, id possible)")
    #error: 0.5 asc -1 5
    if "." in str(sortdesc) or not is_numeric(sortdesc) or (int(sortdesc) != 1 and int(sortdesc) != 0):
        raise HTTPException(400, "sortdesc invalid value (0 and 1 possible)")
    if int(sortdesc) == 0:
        return sortby, "asc"
    return sortby, "desc"

def add_sort(solr_request, sortby, sortdesc):
    if sortby != None:
        sortby, sortdesc = check_sort(sortby, sortdesc)
        return solr_request + f"&sort={sortby} {sortdesc}"
    return solr_request

def map_search_body(body):
    bbox = body.bbox
    collections = body.collections
    ids = body.ids
    sortby = body.sortby[0]["field"]
    sortdesc = body.sortby[0]["direction"]
    if sortdesc == "asc": sortdesc = 0
    else: sortdesc = 1

    if bbox != None:
        bbox = ','.join(str(float) for float in body.bbox)
    if collections != None:
        collections = ','.join(body.collections)
    if ids != None:
        ids = ','.join(body.ids)
    return bbox, collections, ids, sortby, sortdesc

# check limit and start
def check_if_value_is_valid(value, name, default):
    if value != None and is_numeric(value) and int(value) < 0:
        raise HTTPException(400, str(name) + " smaller than 0 prohibited")
    if value == None: return default
    if '?' in str(value): value = value.replace('?', '')
    if not is_numeric(value): return default
    return value


def add_value_to_solr_request(solr_request, value, name, solr_name, default):
    value = check_if_value_is_valid(value, name, default)
    solr_request = add_questions_mark(solr_request)
    solr_request += f"&{solr_name}=" + str(value)
    return solr_request


def add_limit_and_start(solr_request, limit, start, default_limit = config["default_limit"]):
    solr_request = add_value_to_solr_request(solr_request, limit, name= "limit", solr_name= "rows", default = default_limit)
    solr_request = add_value_to_solr_request(solr_request, start, name= "start", solr_name= "start", default = 0)
    return solr_request

def handle_bbox_filter_param(param):
    coords = param.split(',')
    if len(coords) != 4 or any(not is_numeric(c) for c in coords):
        raise HTTPException(400, "Not a valid bbox format")
    if is_not_valid_bbox(coords):
        raise HTTPException(400, "Not a valid bbox format")
    return f"[{coords[1]},{coords[0]} TO {coords[3]},{coords[2]}]"


def handle_datetime_filter_param(param):
    if not is_valid_datetime_param(param):
        raise HTTPException(400, "Not a valid datetime format")
    if '/' not in param:
        return f'"{param}"'
    if param.startswith('../'):
        return param.replace('../', '[* TO ') + "]"
    if param.endswith('/..'):
        return "[" + param.replace('/..', ' TO *]')
    if '/' in param:
        return "[" + param.replace('/', ' TO ') + "]"


def get_filter_query_params(query_params, method):

    # light defense against solr injection (special charaters are espaped and spaces removed)
    for key, item in query_params.items():
        if item != None:
            query_params[key] = escape_user_input(item)

    result = ""
    if not list(query_params.values()).count(None) != len(query_params.values()):
        return result
    result = add_questions_mark(result)
    result += "&fq="
    for key in query_params.keys():
        param = query_params[key]
        if param != None:
            if "collection" in key: key = "collection"
            if "," in param and "collection" in key:
                param = f' OR {key}:'.join(param.split(','))
            if "ids" in key: key = "id"
            if "," in param and "id" in key:
                param = f' OR {key}:'.join(param.split(','))
            elif key == "bbox":
                param = handle_bbox_filter_param(param)
            elif key == "datetime":
                param = handle_datetime_filter_param(param)
            if not result.endswith('fq='):
                result += " AND "
            if key == "datetime": key = "daterange"
            if method == "post":
                result += f"{key}:" + param + " AND type:Feature"
            elif method == "get":
                result += f"{key}:" + param + "&fq=type:Feature"
    return result

def add_questions_mark(result):
    if '?' in result:
        return result
    return result + "?"

def is_numeric(x):
    if isinstance(x, int):
        return True
    return x.replace('.', '', 1).replace('-', '', 1).isdigit()

def is_valid_datetime_param(input_string):
    input_string = input_string.upper()

    split_string = input_string.split('/')

    # Regular expression to match RFC  3339 datetime format
    rfc3339_regex = re.compile(r'^(\d\d\d\d)\-(\d\d)\-(\d\d)(T|t)(\d\d):(\d\d):(\d\d)([.]\d+)?(Z|([-+])(\d\d):(\d\d))$')

    def is_valid_element(s):
        if s in ['', '..']:
            return True
        elif rfc3339_regex.match(s):
            return True
        else:
            return False

    for s in split_string:
        if not is_valid_element(s):
            return False

    try:
        dates = []
        for s in split_string:
            if s and s != '..':
                dates.append(parse_datetime(s))
        # If there is a daterange (2 dates) provided, check if the first date is after (larger than) the second -> 400 bad request
        if len(dates) == 2 and dates[0] > dates[1]:
            return False
    except ValueError:
        return False

    return True

def is_not_valid_bbox(c):
    c = list((float(x) for x in c))
    if c[0] < -180 or c[0] > c[2]:
        return True
    if c[1] < -90 or c[1] > c[3]:
        return True
    if c[2] > 180 or c[2] < c[0]:
        return True
    if c[3] > 90 or c[3] < c[1]:
        return True
    return False
