import logging
from loadbalanced_async_sharded_blockchain.honeybadgerbft.utils import hash
from loadbalanced_async_sharded_blockchain.honeybadgerbft.crypto.threshsig.boldyreva import TBLSPublicKey,TBLSPrivateKey,serialize, group
from collections import defaultdict,deque
from loadbalanced_async_sharded_blockchain.honeybadgerbft.exceptions import CommonCoinFailureException
from loadbalanced_async_sharded_blockchain.honeybadgerbft.clientbase import ClientBase
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
            logger.debug("{} receive message".format(pid))
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
            
            logger.debug("{} collecting shares, {} / {}".format(pid,len(received[round]),f+1))
            if len( received[round]) ==  f+1:
                
                logger.debug("{}:Got enough shares round:{}".format(pid,round))
                signs = dict(list(received[round].items())[:f+1])
                sign =  public_key.combine_shares(signs)

                try:
                    public_key.verify_signature(sign,h)
                except AssertionError:
                    logger.error("Signature verify failed!{}".format((sid,pid,sender,round)))
                    continue

                logger.debug("{} Signature verify success".format(pid))

                bit = hash(serialize(sign))[0] % 2
                output_queue[round].put_nowait(bit)
                logger.debug("{} output coin: {}".format(pid,bit))
    
    broadcast = rpcbase.broadcast_cc
    receive = rpcbase.receive_cc
    
    assert _validate_keys()
    received = defaultdict(dict)
    output_queue = defaultdict(lambda:Queue(1))
    
    Greenlet(_recv).start()

    def get_coin(round,j):
        logger.debug("{} start round:{}".format(pid,round))
        h =  public_key.hash_message(str(( sid, round)))
        message = ("COIN",round,group.serialize( private_key.sign(h),compression=True))
        broadcast(( j,message))
        result = output_queue[round].get()
        logger.debug("{} finish cc phase. result:{}".format(pid,result))
        return result
    
    return get_coin
    