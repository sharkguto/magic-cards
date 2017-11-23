'''
Created on 24 de nov de 2017

@author: gustavo
'''

from sanic import Sanic, response
from sanic.response import json,text
import aiomysql
import asyncio
import uvloop
from sanic.exceptions import RequestTimeout
from aio_pika.robust_connection import connect_robust
import aio_pika
from aio_pika.message import IncomingMessage
import ujson as json
asyncio.set_event_loop_policy(uvloop.EventLoopPolicy())


async def exchange_rabbitmq(messages,queue_name="cards",exchange="cards" ,routing_key="moving_cards"):
    loop = asyncio.get_event_loop()
    connection = await aio_pika.connect("amqp://guest:guest@127.0.0.1/", loop=loop)

    # Creating channel
    channel = await connection.channel()

    # Declaring exchange
    exchange = await channel.declare_exchange(exchange, auto_delete=True)

    # Declaring queue
    queue = await channel.declare_queue(queue_name, auto_delete=True)

    # Binding queue
    await queue.bind(exchange, routing_key)
    posted_cards_queue=0
    for message in messages:
        
        body_val=json.dumps(messages[message]).encode()
        body_key=str(message).encode()
        
        await exchange.publish(
            aio_pika.Message(
                body = body_key+b':=>'+body_val 
            ),
            routing_key
        )
        posted_cards_queue+=1
        
    total_msg =0 
    """while 1:
        try:
            qq= await queue.get(timeout=5)
            total_msg+=1
        except:
            break
    """
    
    # Receiving message
    #incoming_message = await queue.get(timeout=5)

    # Confirm message
    #incoming_message.ack()

    await queue.unbind(exchange, routing_key)
    #await queue.delete()
    await connection.close() 
    return total_msg,posted_cards_queue 
 
def jsonify(fields,records):
    """
    Parse aiomysql record response into JSON format
    """
    #print(records)
    #list_return = []
    
    dict_ret_gethered_id = dict()

    for r in records:
        dict_ret = dict()
        for i in range(len(fields)):
            if 'GathererId'==fields[i]:
                gethered_id=r[i]
            dict_ret[fields[i]]=r[i] if r[i] else 'null' 

        #list_return.append(dict_ret)
        dict_ret_gethered_id[gethered_id]=dict_ret
        
    return dict_ret_gethered_id   
 

async def rabbit_consumer(queue_name="cards",exchange="cards" ,routing_key="moving_cards"):
    loop = asyncio.get_event_loop()
    connection = await aio_pika.connect("amqp://guest:guest@127.0.0.1/", loop=loop)
    # Creating channel
    channel = await connection.channel()

    # Declaring exchange
    exchange = await channel.declare_exchange(exchange, auto_delete=True)

    # Declaring queue
    queue = await channel.declare_queue(queue_name, auto_delete=True)
    await queue.bind(exchange, routing_key)

    total_msg_executed =0
    with open("/tmp/cards_db.txt","a+") as cards_file:
        while 1:
            try:
                incoming_message = await queue.get(timeout=5)
                # Receiving message
                cards_file.write(incoming_message.body.decode()+"\n")
                # Confirm message
                incoming_message.ack()
                total_msg_executed+=1
            except:
                break

    await queue.unbind(exchange, routing_key)
    await queue.delete()
    await connection.close()

app = Sanic()
 
@app.route("/movecards/<expantion_id>",methods=['POST'])
async def hello(request,expantion_id):
    
    try:
        expantion_id = int(expantion_id)
    except:
        return response.html("",404)
    
    loop = asyncio.get_event_loop()
    # fill in with your actual credentials
    conn = await aiomysql.connect(host='127.0.0.1', port=3306,
                              user='root', password='root',
                              db='tcgplace', loop=loop)
    field_names = []
    res = []
    num_cards = 0
    async with conn.cursor() as cur:
        query = 'select * from tcgplace.magiccard where ExpansionId={expantion_id};'.format(expantion_id=expantion_id)
        num_cards = await cur.execute(query)
        field_names = [i[0] for i in cur.description]
        print("RESULTS : ", num_cards)
        res = await cur.fetchall()
        
    results = jsonify(field_names,res)
    if not results:
        return response.html("",404)
    
    exp_name = None
    
    async with conn.cursor() as cur:
        query = 'select name from tcgplace.magicexpansion where ExpansionId={expantion_id};'.format(expantion_id=expantion_id)
        await cur.execute(query)
        res = await cur.fetchall()
        exp_name = res[0][0]
        
    total_cards,posted_cards_queue = await exchange_rabbitmq(messages=results)
    
    conn.close()
    
    return response.json({'expansion_name':exp_name,
                          #'total_cards_queue':total_cards,
                          'num_cards':posted_cards_queue},200)
        
    

@app.route("/moveall",methods=['GET'])
async def moveall(request):
    asyncio.ensure_future(rabbit_consumer())
    return response.html("ok",202)

@app.route("/card/<card_id>",methods=['GET'])
async def get_card(request,card_id):
    
    try:
        card_id = int(card_id)
    except:
        return response.html("",404)
    
    card_ret = None
    with open("/tmp/cards_db.txt","r") as cards_file:
        for lines in cards_file.readlines():
            card_file = lines.split(":=>")
            if card_id == int(card_file[0]):
                card_ret=card_file[1]
                break
    if not card_ret:
        return response.html("",404)
            
    json_render = json.loads(card_ret)
    
    return response.json(json_render,200)


@app.exception(RequestTimeout)
def timeout(request, exception):    
    return response.text('RequestTimeout from error_handler.', 408)



if __name__ == "__main__":
    rabbit_consumer()
    app.run(host="0.0.0.0", workers=2, port=8888)
    
    
    
#Errors 
"""

considerei o GathererId pois nao tinha CardId na tabela 

select CardId from tcgplace.magiccard where ExpansionId=20;

Error Code: 1054. Unknown column 'CardId' in 'field list'
"""
    