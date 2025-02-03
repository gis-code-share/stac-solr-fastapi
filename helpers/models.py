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
    