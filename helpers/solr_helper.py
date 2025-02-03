import requests
import os
import logging

logging.basicConfig(filename='logs/stacapi.log', format='%(asctime)s %(message)s', datefmt='%m/%d/%Y %I:%M %p', level=logging.INFO)

def post(request, body, headers):
    return requests.post(url = request, data = body, headers = headers)

def get(request):
    logging.info(request)
    return requests.get(url = request)