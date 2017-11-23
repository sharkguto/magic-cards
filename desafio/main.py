'''
Created on 23 de nov de 2017

@author: gustavo
'''

from app import app  #, loop
from sanic.config import LOGGING
from desafio.app.controllers.cards import bp_cards

LOGGING['loggers']['network']['handlers'] = [ 'errorSysLog']

app.blueprint(bp_cards)

if __name__ == "__main__":
    app.run(host='127.0.0.1',debug=True,#log_config=False, #LOGGING,
            port=8888,register_sys_signals=True,
            workers=2)