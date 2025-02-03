from fastapi.testclient import TestClient
import  json
from main import app
import pytest

client = TestClient(app)
#pytest  --html-report=./tests/report.html
with open(".\\configuration\\conf.json") as f:
    config = json.load(f)

@pytest.fixture
def test_data():
    root = config["api_root"]
    
    response = client.get(root + "/collections")
    tested_collection_id = response.json()["collections"][0]["id"]
    tested_collection_bbox = response.json()["collections"][0]["extent"]["spatial"]["bbox"][0]
    
    if len(response.json()["collections"]) > 1:
        tested_second_collection_id = response.json()["collections"][1]["id"]
    
    response = client.get(root + "/collections/" + tested_collection_id + "/items")
    tested_item_id = response.json()["features"][0]["id"]
    tested_item_id_2 = response.json()["features"][1]["id"]
    tested_date = response.json()["features"][0]["properties"]["datetime"]
    if tested_date is None: tested_date = response.json()["features"][0]["properties"]["start_datetime"]

    response = client.get( root + "/search?collections=" + tested_collection_id )
    tested_len_search_in_one_coll = response.json()["numberReturned"]

    response = client.get( root + "/search")
    tested_len_all_items = response.json()["numberReturned"]

    response = client.get( root + "/search?datetime=" + tested_date )
    cnt_returned_features = len(response.json()["features"])
    cnt_returned_features_having_the_exact_date = 0
    #cnt_returned_features_having_the_exact_date = len(list(x for x in response.json()["features"] if x["properties"]["datetime"] == test_data["tested_date"] ))
    for feature in response.json()["features"]:
        if "datetime" in feature["properties"].keys() and feature["properties"]["datetime"] == tested_date :
            cnt_returned_features_having_the_exact_date += 1
    if cnt_returned_features_having_the_exact_date != 0:
        tested_len_search_exact_date = cnt_returned_features
    else: tested_len_search_exact_date = None

    response = client.get( root + "/search?datetime=" + tested_date  + "/3080-08-01T00:00:00Z")
    # count of features has to be more (or equal) than the previous test (test_200_get_search_exact_date) because the date is included
    if tested_len_search_exact_date  != None:
        tested_len_search_date_range = len(response.json()["features"])
    else: tested_len_search_date_range = None

    return {
        "root": root,
        "tested_collection_id": tested_collection_id,
        "tested_second_collection_id": tested_second_collection_id,
        "tested_item_id": tested_item_id,
        "tested_item_id_2": tested_item_id_2,
        "tested_date": tested_date,
        "tested_collection_bbox": tested_collection_bbox,
        "tested_len_search_in_one_coll":tested_len_search_in_one_coll,
        "tested_len_all_items": tested_len_all_items,
        "tested_len_search_exact_date": tested_len_search_exact_date,
        "tested_len_search_date_range": tested_len_search_date_range,
        "max_bounds": "-180,-90,180,90"
    }


def test_200_landingpage(test_data):
    response = client.get(test_data["root"] + "/")
    assert response.json()["type"] == "Catalog"
    assert response.status_code == 200

def test_200_get_collections(test_data):
    global tested_collection_id, tested_second_collection_id, tested_collection_bbox
    response = client.get( test_data["root"] + "/collections")
    assert response.status_code == 200
    assert len(response.json()["collections"]) > 0

def test_200_get_collection_id(test_data):
    response = client.get( test_data["root"] + "/collections/" + test_data["tested_collection_id"] )
    assert response.status_code == 200
    assert response.json()["type"] == "Collection"


def test_404_get_non_existent_collection(test_data):
    response = client.get( test_data["root"] + "/collections/" + "coll_non_existent_for_sure")
    assert response.status_code == 404
    assert response.json()["description"] == "Not Found"


def test_200_get_collection_id_items(test_data):
    global tested_item_id, tested_item_id_2, tested_date
    response = client.get( test_data["root"] + "/collections/" + test_data["tested_collection_id"]  + "/items")
    assert response.status_code == 200
    assert response.json()["type"] == "FeatureCollection"
    assert len(response.json()["features"]) > 0

def test_200_get_collection_id_items_id(test_data):
    response = client.get( test_data["root"] + "/collections/" + test_data["tested_collection_id"]  + "/items/" + test_data["tested_item_id"] )
    assert response.status_code == 200
    assert response.json()["type"] == "Feature"
    assert response.json()["collection"] == test_data["tested_collection_id"] 


def test_404_get_non_existent_item(test_data):
    response = client.get( test_data["root"] + "/collections/" + test_data["tested_collection_id"]  + "/items/" + "item_non_existent_for_sure")
    assert response.status_code == 404
    assert response.json()["description"] == "Not Found"

def test_404_get_item_of_non_existent_collection(test_data):
    response = client.get( test_data["root"] + "/collections/" + "coll_non_existent_for_sure" + "/items/" + test_data["tested_item_id"] )
    assert response.status_code == 404
    assert response.json()["description"] == "Not Found"


# with limit
def test_200_get_collections_with_limit(test_data):
    limit = 1
    response = client.get( test_data["root"] + "/collections?limit=" + str(limit))
    assert response.status_code == 200
    assert len(response.json()["collections"]) <= limit
    assert len(response.json()["links"]) > 0 
    assert response.json()["links"][0]["rel"] == "self"


def test_200_get_collection_id_items_with_limit(test_data):
    limit = 1
    response = client.get( test_data["root"] + "/collections/" + test_data["tested_collection_id"]  + "/items?limit=" + str(limit))
    assert response.status_code == 200
    assert response.json()["type"] == "FeatureCollection"
    assert len(response.json()["features"]) == limit


def test_200_get_collections_with_misspelled_limit(test_data):
    limit = 1
    response = client.get( test_data["root"] + "/collections?limiiiit=" + str(limit))
    # limit is ignored
    assert response.status_code == 200
    assert len(response.json()["collections"]) > 0


def test_200_get_collections_with_string_limit(test_data):
    limit = "string"
    response = client.get( test_data["root"] + "/collections?limit=" + str(limit))
    # limit is ignored
    assert response.status_code == 200
    assert len(response.json()["collections"]) > 0


def test_400_get_collections_with_negative_limit(test_data):
    limit = -1
    response = client.get( test_data["root"] + "/collections?limit=" + str(limit))
    assert response.status_code == 400
    assert response.json()["description"] == "limit smaller than 0 prohibited"


def test_404_get_non_existent_endpoint(test_data):
    response = client.get( test_data["root"] + "/desGibtsNet")
    assert response.status_code == 404
    assert response.json()["description"] == "Not Found"


# SEARCH
def test_200_get_search(test_data):
    response = client.get( test_data["root"] + "/search")
    assert response.status_code == 200
    assert response.json()["type"] == "FeatureCollection"
    assert len(response.json()["features"]) > 0

def test_200_get_search_with_limit(test_data):
    limit = 1
    response = client.get( test_data["root"] + "/search?limit=" + str(limit))
    assert response.status_code == 200
    assert response.json()["type"] == "FeatureCollection"
    assert len(response.json()["features"]) == 1

## SEARCH COLLECTIONS
def test_200_get_search_in_one_coll(test_data):
    response = client.get( test_data["root"] + "/search?collections=" + test_data["tested_collection_id"] )
    assert response.status_code == 200
    assert response.json()["type"] == "FeatureCollection"
    assert len(response.json()["features"]) > 0

def test_200_get_search_in_two_colls(test_data):
    if test_data["tested_second_collection_id"]  == "": return
    response = client.get( test_data["root"] + "/search?collections=" + test_data["tested_collection_id"]  + "," + test_data["tested_second_collection_id"] )
    assert response.status_code == 200
    assert response.json()["type"] == "FeatureCollection"
    assert len(response.json()["features"]) > 0
    assert response.json()["numberReturned"] >= test_data["tested_len_search_in_one_coll"]

def test_200_get_search_in_unknown_coll(test_data):
    response = client.get( test_data["root"] + "/search?collections=" + "coll_non_existent_for_sure")
    assert response.status_code == 200
    assert response.json()["type"] == "FeatureCollection"
    assert len(response.json()["features"]) == 0


## SEARCH DATETIME
def test_200_get_search_exact_date(test_data):
    response = client.get( test_data["root"] + "/search?datetime=" + test_data["tested_date"] )
    print(test_data["root"] + "/search?datetime=" + test_data["tested_date"] )
    assert response.status_code == 200
    assert response.json()["type"] == "FeatureCollection"
    cnt_returned_features = len(response.json()["features"])
    assert len(response.json()["features"]) > 0
    cnt_returned_features_having_the_exact_date = 0
    #cnt_returned_features_having_the_exact_date = len(list(x for x in response.json()["features"] if x["properties"]["datetime"] == test_data["tested_date"] ))
    for feature in response.json()["features"]:
        if "datetime" in feature["properties"].keys() and feature["properties"]["datetime"] == test_data["tested_date"] :
            cnt_returned_features_having_the_exact_date += 1
    if cnt_returned_features_having_the_exact_date != 0:
        assert cnt_returned_features_having_the_exact_date == cnt_returned_features
    else:
        assert cnt_returned_features > 0
    

def test_200_get_search_date_range(test_data):
    response = client.get( test_data["root"] + "/search?datetime=" + test_data["tested_date"]  + "/3080-08-01T00:00:00Z")
    assert response.status_code == 200
    assert response.json()["type"] == "FeatureCollection"
    assert len(response.json()["features"]) > 0
    # count of features has to be more (or equal) than the previous test (test_200_get_search_exact_date) because the date is included
    if test_data["tested_len_search_exact_date"]  != None:
        assert len(response.json()["features"]) >= test_data["tested_len_search_exact_date"] 
    else:
        assert len(response.json()["features"]) >= 0

def test_200_get_search_date_range_with_same_date(test_data):
    response = client.get( test_data["root"] + "/search?datetime=" + test_data["tested_date"]  + "/" + test_data["tested_date"] )
    assert response.status_code == 200
    assert response.json()["type"] == "FeatureCollection"
    assert len(response.json()["features"]) > 0
    if test_data["tested_len_search_exact_date"]  != None:
    # count of features has to be equal than the test_200_get_search_exact_date
        assert len(response.json()["features"]) == test_data["tested_len_search_exact_date"] 
    else:
        assert len(response.json()["features"]) > 0


def test_200_get_search_date_to_infinity(test_data):
    response = client.get( test_data["root"] + "/search?datetime=" + test_data["tested_date"]  + "/..")
    assert response.status_code == 200
    assert response.json()["type"] == "FeatureCollection"
    assert len(response.json()["features"]) > 0
    # count of features has to be the same as the previous test (test_200_get_search_date_range) - as long it is not 3080 yet
    if test_data["tested_len_search_exact_date"]  != None:
        assert len(response.json()["features"]) == test_data["tested_len_search_date_range"] 
    else:
        assert len(response.json()["features"]) > 0


def test_200_get_search_infinity_to_date(test_data):
    response = client.get( test_data["root"] + "/search?datetime=../" + test_data["tested_date"] )
    assert response.status_code == 200
    assert response.json()["type"] == "FeatureCollection"
    assert len(response.json()["features"]) > 0
    # count of features has to be more (or equal) than the test_200_get_search_exact_date because the date is included
    if test_data["tested_len_search_exact_date"]  != None:
        assert len(response.json()["features"]) >= test_data["tested_len_search_exact_date"] 
    else:
        assert len(response.json()["features"]) > 0
        

def test_200_get_switched_date_range(test_data):
    #from 2012 to 2002 must return 400 bad request
    response = client.get( test_data["root"] + "/search?datetime=2012-08-01T00:00:00Z/2002-08-01T00:00:00Z")
    assert response.status_code == 400
    assert response.json()["description"] == "Not a valid datetime format"

def test_400_get_search_invalid_date(test_data):
    response = client.get( test_data["root"] + "/search?datetime=2012/08/01T00:00:00Z")
    assert response.status_code == 400
    assert response.json()["description"] == "Not a valid datetime format"

def test_400_get_search_invalid_date_range(test_data):
    response = client.get( test_data["root"] + "/search?datetime=2012-08-01T00:00:00Z/2002:00:00Z")
    assert response.status_code == 400
    assert response.json()["description"] == "Not a valid datetime format"

def test_400_get_search_invalid_date_range_from_infintiy(test_data):
    response = client.get( test_data["root"] + "/search?datetime=../2002:00:00Z")
    assert response.status_code == 400
    assert response.json()["description"] == "Not a valid datetime format"
  
def test_400_get_search_invalid_date_range_to_infintiy(test_data):
    response = client.get( test_data["root"] + "/search?datetime=2002:00:00Z/..")
    assert response.status_code == 400
    assert response.json()["description"] == "Not a valid datetime format"

## SEARCH BBOX
def test_200_get_search_max_bbox(test_data):
    response = client.get( test_data["root"] + "/search?bbox=" + test_data["max_bounds"] )
    assert response.status_code == 200
    assert response.json()["type"] == "FeatureCollection"
    assert len(response.json()["features"]) > 0
    assert len(response.json()["features"]) == test_data["tested_len_all_items"] 

def test_200_get_search_bbox_collection(test_data):
    response = client.get( test_data["root"] + "/search?bbox=" + ",".join(str(float) for float in test_data["tested_collection_bbox"] ))
    assert response.status_code == 200
    assert response.json()["type"] == "FeatureCollection"
    assert len(response.json()["features"]) > 0
    assert response.json()["numberReturned"] == test_data["tested_len_search_in_one_coll"] 


def test_200_get_empty_search_bbox(test_data):
    response = client.get( test_data["root"] + "/search?bbox=1,1,1,1")
    assert response.status_code == 200
    assert response.json()["type"] == "FeatureCollection"
    assert len(response.json()["features"]) == 0

def test_400_get_search_invalid_bbox_two_coords(test_data):
    response = client.get( test_data["root"] + "/search?bbox=33,33")
    assert response.status_code == 400
    assert response.json()["description"] == "Not a valid bbox format"

def test_400_get_search_invalid_bbox_wrong_coords(test_data):
    response = client.get( test_data["root"] + "/search?bbox=-3333,33,33,33")
    assert response.status_code == 400
    assert response.json()["description"] == "Not a valid bbox format"

def test_400_get_search_invalid_bbox_wrong_coords_2(test_data):
    response = client.get( test_data["root"] + "/search?bbox=180,33,90,33")
    assert response.status_code == 400
    assert response.json()["description"] == "Not a valid bbox format"

def test_400_get_search_invalid_bbox_wrong_coords_3(test_data):
    response = client.get( test_data["root"] + "/search?bbox=90,-100,90,-180")
    assert response.status_code == 400
    assert response.json()["description"] == "Not a valid bbox format"

def test_400_get_search_invalid_bbox_wrong_coords_4(test_data):
    response = client.get( test_data["root"] + "/search?bbox=0,180,0,180")
    assert response.status_code == 400
    assert response.json()["description"] == "Not a valid bbox format"

## GET SEARCH ids
def test_200_get_search_with_one_ids(test_data):
    response = client.get( test_data["root"] + "/search?ids=" + test_data["tested_item_id"] )
    assert response.status_code == 200
    assert response.json()["type"] == "FeatureCollection"
    assert len(response.json()["features"]) >= 1

def test_200_get_search_with_two_ids(test_data):
    response = client.get( test_data["root"] + "/search?ids=" + test_data["tested_item_id"]  + "," + test_data["tested_item_id_2"] )
    assert response.status_code == 200
    assert response.json()["type"] == "FeatureCollection"
    assert len(response.json()["features"]) >= 2

def test_200_get_search_with_two_ids_and_date(test_data):
    response = client.get( test_data["root"] + "/search?ids=" + test_data["tested_item_id"]  + "," + test_data["tested_item_id_2"]  + "&datetime=2000-12-31T23:59:59Z/..")
    assert response.status_code == 200
    assert response.json()["type"] == "FeatureCollection"
    assert len(response.json()["features"]) >= 2

def test_200_get_search_with_two_ids_and_collection(test_data):
    response = client.get( test_data["root"] + "/search?ids=" + test_data["tested_item_id"]  + "," + test_data["tested_item_id_2"]  + "&collection="+ test_data["tested_collection_id"] )
    assert response.status_code == 200
    assert response.json()["type"] == "FeatureCollection"
    assert len(response.json()["features"]) >= 2

def test_200_get_search_with_invalidId(test_data):
    response = client.get( test_data["root"] + "/search?ids=thisIsNoItemId")
    assert response.status_code == 200
    assert response.json()["type"] == "FeatureCollection"
    assert len(response.json()["features"]) == 0

## POST SEARCH
def test_200_post_search_all(test_data):
    response = client.post( test_data["root"] + "/search", content = json.dumps({}))
    assert response.status_code == 200
    assert response.json()["type"] == "FeatureCollection"
    assert len(response.json()["features"]) > 0
    assert len(response.json()["features"]) == test_data["tested_len_all_items"] 

def test_200_post_search_one_collection(test_data):
    body = {
      "collections": [test_data["tested_collection_id"] ]
    }
    response = client.post( test_data["root"] + "/search", content = json.dumps(body))
    assert response.status_code == 200
    assert response.json()["type"] == "FeatureCollection"
    assert len(response.json()["features"]) > 0
    assert response.json()["numberReturned"] == test_data["tested_len_search_in_one_coll"] 

def test_200_post_search_two_collections(test_data):
    body = {
      "collections": [test_data["tested_collection_id"] , test_data["tested_second_collection_id"] ]
    }
    response = client.post( test_data["root"] + "/search", content = json.dumps(body))
    assert response.status_code == 200
    assert response.json()["type"] == "FeatureCollection"
    assert len(response.json()["features"]) > 0

def test_200_post_search_exact_date(test_data):
    body = {
      "datetime": test_data["tested_date"] 
    }
    response = client.post( test_data["root"] + "/search", content = json.dumps(body))
    assert response.status_code == 200
    assert response.json()["type"] == "FeatureCollection"
    assert len(response.json()["features"]) > 0
    if test_data["tested_len_search_exact_date"]  != None:
        assert len(response.json()["features"]) == test_data["tested_len_search_exact_date"] 
    else:
        assert len(response.json()["features"]) > 0


def test_200_post_search_bbox(test_data):
    body = {
      "bbox": test_data["max_bounds"] .split(',')
    }
    response = client.post( test_data["root"] + "/search", content = json.dumps(body))
    assert response.status_code == 200
    assert response.json()["type"] == "FeatureCollection"
    assert len(response.json()["features"]) > 0
    assert len(response.json()["features"]) == test_data["tested_len_all_items"] 

def test_200_post_search_with_limit(test_data):
    body = {
      "limit": 1
    }
    response = client.post( test_data["root"] + "/search", content = json.dumps(body))
    assert response.status_code == 200
    assert response.json()["type"] == "FeatureCollection"
    assert len(response.json()["features"]) == 1

def test_200_post_search_wrong_body(test_data):
    body = {
      "unkown_attribute": "test"
    }
    #unkown attributes are ignored, all items return
    response = client.post( test_data["root"] + "/search", content = json.dumps(body))
    assert response.status_code == 200
    assert response.json()["type"] == "FeatureCollection"
    assert len(response.json()["features"]) > 0
    assert len(response.json()["features"]) == test_data["tested_len_all_items"] 

def test_200_post_search_full_body(test_data):
    body = {
        "bbox": [13.995059, 46.512981, 14.035074, 46.524014],
        "datetime": test_data["tested_date"]  + "/..",
        "collections": [
            test_data["tested_collection_id"] ,
            test_data["tested_second_collection_id"] 
        ],
        "limit": 1,
        "ids": [ test_data["tested_item_id"]  ]
    }
    response = client.post( test_data["root"] + "/search", content = json.dumps(body))
    assert response.status_code == 200
    assert response.json()["type"] == "FeatureCollection"
    assert len(response.json()["features"]) <= 1

def test_200_post_search_with_sort(test_data):
    body = {
        "collections": [
            test_data["tested_collection_id"] ,
            test_data["tested_second_collection_id"] 
        ],
        "sortby": [ {"field": "collection", "direction": "asc" } ]
    }
    response_asc = client.post( test_data["root"] + "/search", content = json.dumps(body))
    body["sortby"] = [ {"field": "collection", "direction": "desc" } ]
    response_desc = client.post( test_data["root"] + "/search", content = json.dumps(body))

    assert response_asc.status_code == 200
    assert response_desc.status_code == 200
    assert response_asc.json()["type"] == "FeatureCollection"
    assert response_desc.json()["type"] == "FeatureCollection"
    #Comparing if the first feature in desc has different collection than asc
    assert response_asc.json()["features"][0]["collection"] != response_desc.json()["features"][0]["collection"]

def test_400_post_search_invalid_bbox(test_data):
    body = {
      "bbox": [9000,90213,2002,3]
    }
    response = client.post( test_data["root"] + "/search", content = json.dumps(body))
    assert response.status_code == 400
    assert response.json()["description"] == "Not a valid bbox format"

def test_422_post_search_bbox_not_an_list(test_data):
    body = {
      "bbox": "9000,90213,2002,3"
    }
    response = client.post( test_data["root"] + "/search", content = json.dumps(body))
    assert response.status_code == 422
    assert response.json()["description"] == "value of body attribute is invalid type"

def test_422_post_search_collections_not_a_list(test_data):
    body = {
      "collections": test_data["tested_collection_id"] 
    }
    response = client.post( test_data["root"] + "/search", content = json.dumps(body))
    assert response.status_code == 422
    print(response.json())
    assert response.json()["description"] == "value of body attribute is invalid type"

def test_400_post_search_datetime_not_a_str(test_data):
    body = {
      "datetime": 0
    }
    response = client.post( test_data["root"] + "/search", content = json.dumps(body))
    assert response.status_code == 400
    assert response.json()["description"] == "Not a valid datetime format"


# SORT
def test_200_get_search_with_sort_collection(test_data):
    response = client.get( test_data["root"] + "/search?sortby=collection")
    assert response.status_code == 200
    assert response.json()["type"] == "FeatureCollection"
    assert len(response.json()["features"]) > 0

def test_200_get_search_with_sort_collection_desc(test_data):
    response = client.get( test_data["root"] + "/search?sortby=collection&sortdesc=1")
    assert response.status_code == 200
    assert response.json()["type"] == "FeatureCollection"
    assert len(response.json()["features"]) > 0

def test_200_get_search_with_sort_collection_asc(test_data):
    response = client.get( test_data["root"] + "/search?sortby=collection&sortdesc=0")
    assert response.status_code == 200
    assert response.json()["type"] == "FeatureCollection"
    assert len(response.json()["features"]) > 0

def test_200_get_search_with_sort_datetime(test_data):
    response = client.get( test_data["root"] + "/search?sortby=datetime")
    assert response.status_code == 200
    assert response.json()["type"] == "FeatureCollection"
    assert len(response.json()["features"]) > 0

def test_200_get_search_with_sort_id(test_data):
    response = client.get( test_data["root"] + "/search?sortby=id")
    assert response.status_code == 200
    assert response.json()["type"] == "FeatureCollection"
    assert len(response.json()["features"]) > 0

def test_400_get_search_with_sort_wrong_field(test_data):
    response = client.get( test_data["root"] + "/search?sortby=hello")
    assert response.status_code == 400
    assert response.json()["description"] == "sortby invalid value (collection, datetime, id possible)"

def test_400_get_search_with_negative_sortdesc(test_data):
    response = client.get( test_data["root"] + "/search?sortby=collection&sortdesc=-1")
    assert response.status_code == 400
    assert response.json()["description"] == "sortdesc invalid value (0 and 1 possible)"

def test_400_get_search_with_too_large_sortdesc(test_data):
    response = client.get( test_data["root"] + "/search?sortby=collection&sortdesc=100")
    assert response.status_code == 400
    assert response.json()["description"] == "sortdesc invalid value (0 and 1 possible)"

def test_400_get_search_with_string_sortdesc(test_data):
    response = client.get( test_data["root"] + "/search?sortby=collection&sortdesc=asc")
    assert response.status_code == 400
    assert response.json()["description"] == "sortdesc invalid value (0 and 1 possible)"

def test_400_get_search_with_float_sortdesc(test_data):
    response = client.get( test_data["root"] + "/search?sortby=collection&sortdesc=0.5")
    assert response.status_code == 400
    assert response.json()["description"] == "sortdesc invalid value (0 and 1 possible)"

def test_200_get_items_with_sort_datetime(test_data):
    response = client.get( test_data["root"] + "/collections/" + test_data["tested_collection_id"]  + "/items?sortby=datetime")
    assert response.status_code == 200
    assert response.json()["type"] == "FeatureCollection"
    assert len(response.json()["features"]) > 0

def test_200_get_items_with_sort_datetime_desc(test_data):
    response = client.get( test_data["root"] + "/collections/" + test_data["tested_collection_id"]  + "/items?sortby=datetime&sortdesc=1")
    assert response.status_code == 200
    assert response.json()["type"] == "FeatureCollection"
    assert len(response.json()["features"]) > 0
