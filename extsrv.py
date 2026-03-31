import websockets
import asyncio,json
out=print
class WebSocketServer:
    def __init__(self,host='localhost',port=14431,send=print):
        self.host,self.port=host,port
        self.send=send
        self.clients=[]
    async def acc(self,webs):
        self.clients.append(webs)
        async for mess in webs:
            self.send(json.loads(mess)['finalUrl'])
    async def bnd(self):
        async with websockets.serve(self.acc,self.host,self.port):
            out('mhext服务已启动')
            await asyncio.Future()
    def start(self):
        while 1:
            try:asyncio.run(self.bnd())
            except Exception as e:out(e)   
if __name__=='__main__':
    server=WebSocketServer('localhost', 14431)
    server.start()
