import logging
from loadbalanced_async_sharded_blockchain.honeybadgerbft.utils import hash
from loadbalanced_async_sharded_blockchain.honeybadgerbft.crypto.threshsig.boldyreva import TBLSPublicKey,TBLSPrivateKey,serialize, group
from collections import defaultdict
from loadbalanced_async_sharded_blockchain.honeybadgerbft.exceptions import CommonCoinFailureException
from loadbalanced_async_sharded_blockchain.honeybadgerbft.clientbase import ClientBase
from gevent.queue import Queue
import gevent

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
            logger.error("invalid sender value:{}".format(sender))
            return False
        
        if round < 0:
            logger.error("invalid round value:{}".format(round))
            return False
        
        if sender in received[round]:
            logger.error("redundant coin sig received：{} round:{} received:{}".format(pid,round,received))
            return False
        return True
    
    def _meet_share_condition(r,received,f):
        return len( received[r]) ==  f+1
    
    def _recv():
        while True:
            sender, (_, r, sign_serialized) = receive(j) 
            assert _message_check(sender,r)
            assert isinstance(sign_serialized, bytes)
            logger.debug("{} receive instance{}'s cc message".format(pid,j))
            
            sign = group.deserialize(sign_serialized,compression=True)
            h = public_key.hash_message(str((sid,r)))
            try:
                # when current sid != message sid or current r != message r will fail.
                public_key.verify_share(sign,sender,h)
            except AssertionError:
                logger.warn("{} pk verify_share failed in round {}!".format(pid, r))
                continue
            
            received[r][sender] = sign
            
            logger.debug("{} collecting shares, {} / {}".format(pid,len(received[r]),f+1))
            if _meet_share_condition(r,received,f):
                signs = dict(list(received[r].items())[:f+1])
                combined_sign =  public_key.combine_shares(signs)
                try:
                    public_key.verify_signature(combined_sign,h)
                except AssertionError:
                    logger.error("{} instance:{} pk verify_signature failed in round:{}!".format(pid,j,r))
                    continue

                bit = hash(serialize(combined_sign))[0] % 2
                output_queue[r].put_nowait(bit)

    def get_coin(round,j):
        logger.debug("{} start round:{}".format(pid,round))
        h =  public_key.hash_message(str(( sid, round)))
        message = ("COIN", round, group.serialize( private_key.sign(h),compression=True))
        broadcast(( j,message))

        result = output_queue[round].get()
        logger.debug("{} finish cc. result:{}".format(pid,result))
        return result

    broadcast = rpcbase.broadcast_cc
    receive = rpcbase.receive_cc
    assert _validate_keys()
    
    received = defaultdict(dict)
    output_queue = defaultdict(lambda:Queue(1))
    gl = gevent.spawn(_recv)
    return get_coin, gl
    