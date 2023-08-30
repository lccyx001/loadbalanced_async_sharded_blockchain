import zerorpc
import logging
from utils import hash
from crypto.threshsig.boldyreva import TBLSPublicKey,TBLSPrivateKey,serialize, group
from collections import defaultdict,deque
import gevent

logging.basicConfig(level=logging.INFO,filename="log.log")
logger = logging.getLogger(__name__)

class CommonCoinFailureException(Exception):
    """Raised for common coin failures."""
    pass

class CommonCoin(object):

    def __init__(self,instance_id,local_id,N,f,
                 public_key:TBLSPublicKey,private_key:TBLSPrivateKey,
                 broadcast_channels) -> None:
        self.instance_id = instance_id
        self.local_id = local_id
        self.N = N
        self.f = f
        self.public_key=public_key
        self.private_key=private_key
        self.broadcast_channel=broadcast_channels
        self.received = defaultdict(dict)
        self.output_queue = defaultdict(lambda:deque(maxlen=1)) 
        self.remote_channel = []
        self.server = None
        self.green_let = None
        assert self._validate() == True
        

    def _validate(self):        
        if self.public_key.k != self.f+1:
            return False
        if self.public_key.l != self.N:
            return False
        return True

    def connect_all(self,):
        for address in self.broadcast_channel:
            client = zerorpc.Client()
            client.connect(address)
            self.remote_channel.append(client)
            logging.info("common coin server {} connected to {}".format(self.local_id, address))

    # def list_remote_channel(self):

    def _broadcast(self,sender,message):
        logger.info("node:{} broad cast message: {}".format(sender,message))
        for client in self.remote_channel:
            flag = client.recv(sender,
                        message["msg_type"],
                        message["round"],
                        message["sign"])
            if not flag:
                logger.error("local_id:{} ,remote failed".format(self.local_id))

    def recv(self,sender,msg_type,round,sign):
        if sender not in range(self.N):
            logger.error("invalid sender value")
            return False
        if round < 0:
            logger.error("invalid round value")
            return False
        if sender in self.received[round]:
            logger.info("redundant coin sig received：{}".format((self.instance_id,self.local_id,sender,round)))
            return True
        sign = group.deserialize(sign,compression=True)
        
        logger.info("recv making hash message:({},{})".format(self.instance_id,round))
        h = self.public_key.hash_message(str((self.instance_id,round)))

        try:
            self.public_key.verify_share(sign,sender,h)
        except AssertionError:
            logger.error("Signature share failed! {}".format((self.instance_id,self.local_id,sender,round)))
            return False
        
        self.received[round][sender] = sign
        if len(self.received[round]) == self.f+1:
            logger.info("instance{}:Got enough shares".format(self.local_id))
            
            signs = dict(list(self.received[round].items())[:self.f+1])
            sign = self.public_key.combine_shares(signs)
            logger.info("instance{}:Finish combine shares".format(self.local_id))

            try:
                self.public_key.verify_signature(sign,h)
            except AssertionError:
                logger.error("Signature verify failed!{}".format((self.instance_id,self.local_id,sender,round)))
                return False
            logger.info("instance{}:Signature verify success")

            bit = hash(serialize(sign))[0] % 2
            self.output_queue[round].append(bit)
            logger.info("instance{}:CommonCoin is {}".format(self.local_id,bit))
            return True
        logger.info("instance {}: Waiting for enough shares,now {}, expert {}".format(self.local_id,self.received[round],self.f+1))
        return True

    def get_coin(self,round):
        logger.info("making hash message:({},{})".format(self.instance_id,round))

        h = self.public_key.hash_message(str((self.instance_id, round)))
        message = {"msg_type":"COIN","round":round,"sign":group.serialize(self.private_key.sign(h),compression=True)}

        self._broadcast(sender=self.local_id,message=message)
        # print("************",self.output_queue[round])
        if len(self.output_queue[round])>0:
            return self.output_queue[round][0]
        return None

    def run_forever(self,host,port):
        server = zerorpc.Server(self)
        address = "tcp://{}:{}".format(host,port)
        server.bind(address)
        logger.info("starting common coin server :{}".format(self.local_id))
        server.run()
        


    def stop(self):
        logger.info("stop common coin server:{}".format(self.local_id))
        self.green_let.kill()
        