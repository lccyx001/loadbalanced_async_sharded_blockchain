import zerorpc
import gevent
import logging
logger = logging.getLogger(__name__)
logging.basicConfig(level=logging.INFO,filename="log.log")

class RPCBase(object):

    def __init__(self,broadcast_channels,host,port) -> None:
        self.broadcast_channel = broadcast_channels
        self.remote_channels = dict()
        self.greenlet = None
        self.host = host
        self.port =port
        
    
    def connect_broadcast_channel(self):
        if not self.remote_channels:
            logger.info("connect to:{}".format(self.broadcast_channel))
            for id,adress in self.broadcast_channel:
                client = zerorpc.Client()
                client.connect(adress)   
                self.remote_channels[id] = [adress,client]

    def run_forever(self):
        server = zerorpc.Server(self)
        server.bind("tcp://{}:{}".format(self.host,self.port))
        self.greenlet = gevent.spawn(server.run)
        logger.info("start server:{}:{}".format(self.host,self.port))
        self.greenlet.join()

    def stop(self):
        self.greenlet.kill()

    def echo(self):
        print("echo:",self.host,self.port)
        