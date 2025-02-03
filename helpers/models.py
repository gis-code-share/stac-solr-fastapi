from pydantic import BaseModel

class SearchBody(BaseModel):
    bbox: list = None
    datetime: str = None
    collections: list = None
    limit: int = None
    ids: list = None
    sortby: list = [ {"field": None, "direction": "asc" } ]
    start: int = 0

