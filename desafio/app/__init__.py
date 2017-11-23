from sanic import Sanic
from sanic import response
from sanic.config import Config
from sanic.exceptions import RequestTimeout,NotFound
import configparser

import logging
from logging import handlers
import socket
from datetime import datetime
import requests

import asyncio
import uvloop
import aiomysql

asyncio.set_event_loop_policy(uvloop.EventLoopPolicy())
loop = asyncio.get_event_loop()



#routing_key = "queue name"

app = Sanic(__name__)
# remove logo
app.config.LOGO = None
Config.REQUEST_TIMEOUT = 60


    
def jsonify(records):
    """
    Parse aiomysql record response into JSON format
    """
    #print(records)
    list_return = []
    
    for r in records:
        itens = r.items()
        list_return.append({i[0]:i[1].rstrip() if type(i[1])==str else i[1] for i in itens})
    return list_return    

@app.exception(RequestTimeout)
def timeout(request, exception):    
    return response.text('RequestTimeout from error_handler.', 408)

@app.exception(NotFound)
def not_found(request, exception):
    """remove error for favicon.ico"""

    if "favicon.ico" in str(exception):
        return response.text('icon does not exists', 404)
    else:
        return response.text('Route does not exists', 404)
    
@app.listener('before_server_start')
async def register_log(app, loop):
    # Create a database connection pool
    app.config['pool'] = await aiomysql.create_pool(host='127.0.0.1', port=3306,
                                      user='root', password='root',
                                      db='tcgplace', loop=loop,minsize=1,maxsize=3)
    
    
    app.api_logger = logging.getLogger('magic')
    if (len(app.api_logger.handlers) == 0):
        _tmp_folder = "/tmp/"
        LOG_BASE_NAME = "magic"
        LOG_SUFIX = '.log'
        LOG_FORMAT = '%(asctime)-15s %(levelname)s [%(username)s %(ip)s] - %(message)s'
        formatter = logging.Formatter(LOG_FORMAT)
        #main log
        app.api_logger.setLevel(logging.DEBUG)
        log_file_handler = handlers.TimedRotatingFileHandler(LOG_BASE_NAME+LOG_SUFIX, when='D', interval=1, backupCount=365, encoding='UTF-8', delay=False, utc=True)
        log_file_handler.setFormatter(formatter)
        app.api_logger.addHandler(log_file_handler)
    
    try:
        app.api_logger.info("start running %r %s at %s",app,socket.gethostname(),datetime.now(),extra={'username': 'sanic','ip': socket.gethostbyname(socket.gethostname())})
    except:
        #log rotate
        app.api_logger.info("start running %r %s at %s",app,socket.gethostname(),datetime.now(),extra={'username': 'sanic','ip': socket.gethostbyname(socket.gethostname())})



async def requests_async(url,data,params,headers,libexec=requests.get):
    
    params_data = dict(url=url,json=data,params=params,headers=headers)
    futures = [
        loop.run_in_executor(
            None, 
            lambda: libexec(**params_data),            
        )
    ]
    response_req = await asyncio.gather(*futures)
    
    return response_req[0]

