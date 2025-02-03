
import json
from starlette.exceptions import HTTPException
from helpers import links


with open('.\\configuration\\map.json', 'r') as file:
    global_map = json.load(file)

with open(".\\configuration\\conf.json") as f:
    config = json.load(f)


def change_key_name(dict, old, new):
    if not old in dict.keys(): raise Exception("Key not in dict")
    dict[new] = dict.pop(old)
    return dict

def map_single_attribute(attribute, response, map):
    listKey = False
    r = response.copy()
    for key in map[attribute]:
        if "list:" in str(key) or listKey != False:
            if listKey == False:
                listKey = key.replace('list:', '')
                continue
            if "json:" in str(key):
                key = key.replace('json:', '')
                r[listKey] = [json.loads(o[key]) for o in r[listKey]]
            else:
                r[listKey] = [o[key] for o in r[listKey]]
        elif "json:" in str(key):
            key = key.replace('json:', '')
            r = json.loads(r[key])
        else:
            if isinstance(key, int) and key >= len(r):
                raise HTTPException(404, "Not Found")
            r = r[key]
    if listKey != False: return r[listKey]
    return r

def map_solr_to_api(response, url, method, code, request):
    url = url.replace(config["api_root"], '')
    map =  global_map["paths"][url][method]["responses"][code]
    for attribute in map:
        if isinstance(map[attribute], list):
            if attribute == "response":
                response = map_single_attribute("response", response, map)
            else:
                response[attribute] = map_single_attribute(attribute, response, map)
        elif map[attribute] == "":
            del response[attribute]
        elif map[attribute].startswith('len:'):
            len_of = map[attribute].replace('len:', '')
            response[attribute] = len(response[len_of])
        else:
           change_key_name(response, map[attribute], attribute) 
    return links.add_general_links(response, request)