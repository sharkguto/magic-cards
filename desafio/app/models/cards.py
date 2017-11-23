'''
Created on 23 de nov de 2017

@author: gustavo
'''
from desafio.app import app

class Cards(object):
    '''
    Cards model
    '''


    def __init__(self,request):
        '''
        Constructor
        '''
        self._request = request
        
    async def post_movecards(self,expantion_id):
        pool = self._request.app.config['pool']
        async with pool.acquire() as conn:
            query = 'select * from tcgplace.magiccard where ExpansionId={expantion_id};'.format(expantion_id=expantion_id)
            results = await conn.fetch(query)
        #return response.json({'posts': results})
        return app.jsonify(results)
        