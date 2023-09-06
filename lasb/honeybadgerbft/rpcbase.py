import zerorpc
import gevent
from gevent.queue import Queue
import logging
logger = logging.getLogger(__name__)
logging.basicConfig(level=logging.INFO,filename="log.log")

class RPCBase(object):

    def __init__(self,broadcast_channels,host,port,N,id) -> None:
        self.broadcast_channel = broadcast_channels
        self.id = id
        self.remote_channels = dict()
        self.greenlet = None
        self.host = host
        self.port =port
        
        # used in cc
        self.coin_recvs = [Queue() for _ in range(N)]  

        # used in ba
        self.aba_recvs = [Queue() for _ in range(N)] # ba use this queue to exchange message
        self.aba_outputs = [Queue(1) for _ in range(N)] # ba output a value when finish and save it in this queue
        self.aba_inputs = [Queue(1) for _ in range(N)] # ba receive a upper input and save in this queue

        # used in rbc
        self.rbc_recvs = [Queue() for _ in range(N)] # rbc use this queue to exchange message
        self.rbc_outputs = [Queue(1) for _ in range(N)] # rbc output value when finish and save it in this queue
        self.rbc_input = Queue() # only rbc leader will call this queue to receive input

    def connect_broadcast_channel(self):
        logger.info("connect to:{}".format(self.broadcast_channel))
        if not self.remote_channels:
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

    def recv(self,raw_message):
        logger.debug("recv:{}".format(raw_message))
        (sender,(tag,(j,msg))) = raw_message
        if tag == "ACS_COIN": self.coin_recvs[j].put_nowait((sender,msg))
        if tag == "ACS_ABA": self.aba_recvs[j].put_nowait((sender,msg))
        if tag == "ACS_RBC": self.rbc_recvs[j].put_nowait((sender,msg))
        # rbc_lens = [len(_) for _ in self.rbc_recvs]
        # logger.debug("{} rbc_recvs queue len:{}".format(self.id,rbc_lens))

    ### cc ###
    def broadcast_cc(self,message):
        """
        :param message: (j, content) 
        j is the query index
        """
        assert len(message) == 2
        for target_id,(adress,client) in self.remote_channels.items():
            logger.info("{} broadcast to:{}".format(self.id,target_id))
            raw_message = (self.id, ('ACS_COIN', message))
            client.recv(raw_message)
     
    def receive_cc(self,j):
        result = self.coin_recvs[j].get()
        logger.debug("{} index:{} receive_cc {}".format(self.id,j,result))
        return result
        
    #### ba ####
    def broadcast_ba(self,message):
        """
        :param message: 
        In EST phase form of (j, ('EST', round, est_value))
        In AUX phase form of (j, ('AUX', round, w))
        In CONF phase form of (j, ('CONF', epoch, tuple(bin_values[epoch])))
        """
        assert len(message) == 2
        for target_id,(adress,client) in self.remote_channels.items():
            logger.info("{} broadcast to:{}".format(self.id,target_id))
            raw_message = (self.id, ('ACS_ABA', message))
            client.recv(raw_message)
        return True
    
    def receive_ba(self,j):
        result = self.aba_recvs[j].get()
        logger.debug("{} index:{} receive_ba {}".format(self.id,j,result))
        return result

    def input_ba(self,j):
        """
        :param message: (sender , message content)
        """
        result = self.aba_inputs[j].get()
        logger.debug("{} index:{} input_ba {}".format(self.id,j,result))
        return result
    
    def output_ba(self,vi,j):
        logger.debug("{} output_ba {} in queue {}".format(self.id,vi,j))
        self.aba_outputs[j].put_nowait(vi)
    
    #### rbc ####
    def broadcast_rbc(self,message):
        """
        :param message: 
        In VAL phase form of (j,('ECHO', roothash, branch, stripe)) 
        In ECHO phase form of (j,('READY', roothash))
        In READY phase form of (j, ('READY', roothash))
        """
        assert len(message) == 2
        for target_id,(adress,client) in self.remote_channels.items():
            logger.info("{} broadcast to:{}".format(self.id,target_id))
            raw_message = (self.id, ('ACS_RBC', message))
            client.recv(raw_message)
        return True
    
    def send_rbc(self, target_id, message, j):
        """
        RPC leader use this function
        :param target_id: target instance pid
        :param message: form of ('VAL', roothash, branch, stripes[i], i) 
        :param j: index of rbc_recvs queue 
        :param piece_idx: index of rbc stripes
        """
        assert len(message) == 5
        logger.debug("{} send to {} message:{}".format(self.id,target_id,message))
        
        raw_message = (self.id,("ACS_RBC",(j,message)))
        if not self.remote_channels.get(target_id):
            # send piece to self
            self.recv(raw_message)
            return True
        
        address, client = self.remote_channels[target_id]
        client.recv(raw_message)
        return True
    
    def receive_rbc(self,j):
        result = self.rbc_recvs[j].get()
        logger.debug("{} index:{} receive_rbc {}".format(self.id,j,result))
        return result
    
    def input_rbc(self):
        result = self.rbc_input.get()
        logger.debug("{} input_rbc {}".format(self.id,result))
        return result
    
    def rbc_in(self,m,j):
        logger.debug("{} index:{} rbc_in {}".format(self.id,j,m))
        self.rbc_outputs[j].put_nowait(m)

    #### acs ####
    def rbc_out(self,j):
        result = self.rbc_outputs[j].get()
        logger.info("{} index:{} rbc_outputs {}".format(self.id,j,result))
        return result

    def aba_in(self,vi,j):
        logger.info("{} index:{} aba_in {}".format(self.id,j,vi))
        self.aba_inputs[j].put_nowait(vi)
    
    def aba_out(self,j):
        result = self.aba_outputs[j].get()
        logger.info("{} index:{} aba_out {}".format(self.id,j,result))
        return result
    
    #### no use ####
    def input_rbc_insert(self,message):
        logger.info("{} acs get input {}".format(self.id,message))
        self.rbc_input.put(message)