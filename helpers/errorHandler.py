from fastapi.responses import JSONResponse
import logging
logging.basicConfig(filename='logs/stacapi.log', format='%(asctime)s %(message)s', datefmt='%m/%d/%Y %I:%M %p', level=logging.INFO)

def errorResponse(response=None, code=None, description=None, serverError=False):
    if serverError:
        code = "500"
        logging.error(" SERVER ERROR: " + str(description))
        description = "Server Error"
    elif response != None:
        code = str(response.status_code)
        print(response.content)
        if "msg=" in str(response.content):
            description = str(response.content).split('msg=')[1].split(',code')[0]
    
    if code != 500:
        logging.info(" INFO: faulty request from client " + str(description))
    return JSONResponse(status_code= int(code), content={
        "code": code,
        "description": description
    })