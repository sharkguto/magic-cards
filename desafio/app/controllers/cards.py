'''
Created on 23 de nov de 2017

@author: gustavo
'''


from sanic import response
from sanic import Blueprint
from app import app
from desafio.app.models.cards import Cards

bp_cards = Blueprint('cards')

@bp_cards.route('/movecards/<expantion_id>',methods=['POST','GET'])
async def bp_move_card(request,expantion_id):
    """
    route movecards by expantion_id
    Brings all cards related with expantion_id desired
    :param request: request object from sanic
    :type request: dict | bytes
    :param expantion_id: filter cards by expantion_id from table magiccard 
    :type expantion_id: int

    :rtype: dict | bytes
    """
    
    try:
        expantion_id = int(expantion_id)
    except:
        return response.html("",404)
    cards = Cards(request)
    result = cards.post_movecards(expantion_id)
    app.api_logger.info("URL: [%r] %s" , # @UndefinedVariable
                        request.method,request.url,
                        extra={'username': 'guest','ip': 
                               request.headers['remote_addr'] if 'remote_addr' in request.headers else request.ip})  
    return response.json(result,200)


@bp_cards.route('/card/<card_id>',methods=['GET'])
async def bp_view_card(request,card_id):
    """
    route card by card_id
    Brings all data from card requested
    :param request: request object from sanic
    :type request: dict | bytes
    :param card_id: filter cards by card_id from a text file 
    :type card_id: int

    :rtype: dict | bytes
    """
    cards = Cards(request)
    results = await cards.get_card(card_id=card_id)
    app.api_logger.info("URL: [%r] %s" , # @UndefinedVariable
                        request.method,request.url,
                        extra={'username': 'guest','ip': 
                               request.headers['remote_addr'] if 'remote_addr' in request.headers else request.ip})  
    return response.json(results,200)
