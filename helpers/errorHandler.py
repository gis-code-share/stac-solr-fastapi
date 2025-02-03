from fastapi.responses import JSONResponse
import logging
logging.basicConfig(filename='logs/stacapi.log', format='%(asctime)s %(message)s', datefmt='%m/%d/%Y %I:%M %p', level=logging.INFO)

def errorResponse(response=None, code=None, description=None, serverError=False):
    if serverError:
        tb = description.__traceback__
        code = "500"
        logging.error(" SERVER ERROR: " + str(description) + f" File: {tb.tb_frame.f_code.co_filename}")
        
        print(f"Server Error: {str(description)}")
        print(f"Line number: {tb.tb_lineno}")
        print(f"File: {tb.tb_frame.f_code.co_filename}")
        print(f"Function: {tb.tb_frame.f_code.co_name}")
        
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