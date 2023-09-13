import logging
from utils import hash
from crypto.threshsig.boldyreva import TBLSPublicKey,TBLSPrivateKey,serialize, group
from collections import defaultdict,deque
from exceptions import CommonCoinFailureException
from clientbase import ClientBase
from gevent.queue import Queue
from gevent import Greenlet

logging.basicConfig(level=logging.DEBUG,filename="log.log")
logger = logging.getLogger(__name__)


def commoncoin(sid,pid,N,f,public_key:TBLSPublicKey,private_key:TBLSPrivateKey,rpcbase:ClientBase,j):
    """A shared coin based on threshold signatures

    :param sid: a unique instance id
    :param pid: my id number
    :param N: number of parties
    :param f: fault tolerance, :math:`f+1` shares needed to get the coin
    :param PK: ``boldyreva.TBLSPublicKey``
    :param SK: ``boldyreva.TBLSPrivateKey``
    :param rpcbase: RPCBase client 
    :param j: RPCBase query index
    :return: a function ``getCoin()``, where ``getCoin(r)`` blocks
    """
    def _validate_keys():
        if public_key.k != f+1:
            return False
        if public_key.l != N:
            return False
        return True
    
    def _message_check(sender,round):
        if sender not in range(N):
            logger.warn("invalid sender value:{}".format(sender))
            return False
        
        if round < 0:
            logger.warn("invalid round value:{}".format(round))
            return False
        
        if sender in received[round]:
            logger.warn("redundant coin sig received：{}".format(pid))
            return False
        return True
    
    def _recv():
        while True:
            sender, (msg_type,round,sign) = receive(j) 
            logger.info("{} receive message".format(pid))
            if not _message_check(sender,round):
                continue
            
            sign = group.deserialize(sign,compression=True)

            h = public_key.hash_message(str((sid,round)))

            try:
                public_key.verify_share(sign,sender,h)
            except AssertionError:
                logger.error("{} signature share failed in round {}!".format(pid, round))
                continue
            
            received[round][sender] = sign
            
            logger.info("{} collecting shares, {} / {}".format(pid,len(received[round]),f+1))
            if len( received[round]) ==  f+1:
                
                logger.info("{}:Got enough shares round:{}".format(pid,round))
                signs = dict(list(received[round].items())[:f+1])
                sign =  public_key.combine_shares(signs)

                try:
                    public_key.verify_signature(sign,h)
                except AssertionError:
                    logger.error("Signature verify failed!{}".format((sid,pid,sender,round)))
                    continue

                logger.info("{} Signature verify success".format(pid))

                bit = hash(serialize(sign))[0] % 2
                output_queue[round].put_nowait(bit)
                logger.info("{} output coin: {}".format(pid,bit))
    
    broadcast = rpcbase.broadcast_cc
    receive = rpcbase.receive_cc
    
    assert _validate_keys()
    received = defaultdict(dict)
    output_queue = defaultdict(lambda:Queue(1))
    
    Greenlet(_recv).start()

    def get_coin(round,j):
        logger.info("{} start round:{}".format(pid,round))
        h =  public_key.hash_message(str(( sid, round)))
        message = ("COIN",round,group.serialize( private_key.sign(h),compression=True))
        broadcast(( j,message))
        result = output_queue[round].get()
        logger.info("{} finish cc phase.".format(pid))
        return result
    
    return get_coin
    