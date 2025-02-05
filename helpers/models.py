from pydantic import BaseModel
from fastapi import Request

class SearchBody(BaseModel):
    bbox: list = None
    datetime: str = None
    collections: list = None
    limit: int = None
    ids: list = None
    sortby: list = [ {"field": None, "direction": "asc" } ]
    start: int = 0


class LinkParameters():
    request: Request = None
    start: int = None
    numberMatched: int = None
    numberReturned: int = None
    limit: int = None
    
    def __init__(self, request: Request = None, start: int = None, numberMatched: int = None, numberReturned: int = None, limit: int = None):
        self.request = request
        self.start = start
        self.numberMatched = numberMatched
        self.numberReturned = numberReturned
        self.limit = limit
    
class SearchParameters():
    request: Request = None
    bbox: list = None
    datetime: str = None
    collections: str = None
    limit: int = None
    ids: str = None
    sortby: str = None
    sortdesc: int = 0
    start: int = 0
    
    def __init__(self, request: Request = None, bbox: list = None, datetime: str = None, collections: str = None, limit: int = None, ids: str = None, sortby: str = None, sortdesc: int = 0, start: int = 0):
        self.request = request
        self.bbox = bbox
        self.datetime = datetime
        self.collections = collections
        self.limit = limit
        self.ids = ids
        self.sortby = sortby
        self.sortdesc = sortdesc
        self.start = start
        
    def initCollsAndIds(self, request: Request = None, collections: str = None, ids: str = None):
        self.request = request
        self.collections = collections
        self.ids = ids
    
    def initWithSearchBody(self, sb: SearchBody):
        self.bbox = sb.bbox
        self.datetime = sb.datetime
        self.collections = sb.collections
        self.limit = sb.limit
        self.ids = sb.ids
        self.sortby = str(sb.sortby)
        self.start = sb.start

