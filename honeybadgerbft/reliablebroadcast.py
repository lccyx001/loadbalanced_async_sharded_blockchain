# coding=utf-8
from collections import defaultdict
from loadbalanced_async_sharded_blockchain.honeybadgerbft.utils import ErasureCode,merkleTree,getMerkleBranch,merkleVerify
import logging
from loadbalanced_async_sharded_blockchain.honeybadgerbft.clientbase import ClientBase
import gevent
from gevent.queue import Queue
from gevent.event import Event
logger = logging.getLogger(__name__)
logging.basicConfig(level=logging.INFO,filename="log.log")

def _decode_output(roothash,K,N,stripes):
    # Rebuild the merkle tree to guarantee decoding is correct
    m = ErasureCode.decode(K, N, stripes[roothash])
    _stripes = ErasureCode.encode(K, N, m)
    _mt = merkleTree(_stripes)
    _roothash = _mt[1]
    assert _roothash == roothash
    return m

def _statisfy_echo_condition(roothash,echoCounter,EchoThreshold,readySent):
    return echoCounter[roothash] >= EchoThreshold and not readySent.is_set()

def _statisfy_ready_condition(roothash,ready,ReadyThreshold,readySent):
    return len(ready[roothash]) >= ReadyThreshold and not readySent.is_set()

def _statisfy_output_condition(roothash,ready,OutputThreshold,echoCounter,K):
    return len(ready[roothash]) >= OutputThreshold and echoCounter[roothash] >= K

def reliablebroadcast(sid, pid, N, f, leader, rpcbase:ClientBase,query_index):
    """Reliable broadcast

    :param int pid: ``0 <= pid < N``
    :param int N:  at least 3
    :param int f: fault tolerance, ``N >= 3f + 1``
    :param int leader: ``0 <= leader < N``
    :param rpcbase: used for communcation
    :param query_index:query index used in rpcbase
    
    :return str: ``m`` after receiving :math:`2f+1` ``READY`` messages
        and :math:`N-2f` ``ECHO`` messages

        .. important:: **Messages**

            ``VAL( roothash, branch[i], stripe[i] )``
                sent from ``leader`` to each other party
            ``ECHO( roothash, branch[i], stripe[i] )``
                sent after receiving ``VAL`` message
            ``READY( roothash )``
                sent after receiving :math:`N-f` ``ECHO`` messages
                or after receiving :math:`f+1` ``READY`` messages
    """        
    
        
                
    input = rpcbase.input_rbc if pid == leader else None
    receive = rpcbase.receive_rbc
    send = rpcbase.send_rbc
    broadcast = rpcbase.broadcast_rbc

    assert N >= 3*f + 1
    assert f >= 0
    assert 0 <= leader < N
    assert 0 <= pid < N

    K               = N - 2 * f  # Need this many to reconstruct. (# noqa: E221)
    EchoThreshold   = N - f      # Wait for this many ECHO to send READY. (# noqa: E221)
    ReadyThreshold  = f + 1      # Wait for this many READY to amplify READY. (# noqa: E221)
    OutputThreshold = 2 * f + 1  # Wait for this many READY to output
    # NOTE: The above thresholds  are chosen to minimize the size
    # of the erasure coding stripes, i.e. to maximize K.
    # The following alternative thresholds are more canonical
    # (e.g., in Bracha '86) and require larger stripes, but must wait
    # for fewer nodes to respond
    #   EchoThreshold = ceil((N + f + 1.)/2)
    #   K = EchoThreshold - f
    stripes = defaultdict(lambda: [None for _ in range(N)])

    echoCounter = defaultdict(lambda: 0)
    echoSenders = set()  # Peers that have sent us ECHO messages

    ready = defaultdict(set)
    readySent = Event()
    readySent.clear()

    readySenders = set()  # Peers that have sent us READY messages

    if pid == leader:
        # The leader erasure encodes the input, sending one strip to each participant
        m = input()  # block until an input is received
        assert isinstance(m,(str,bytes))
        logger.info("{} received {} bytes.".format(pid,len(m)))

        broadcast_stripes = ErasureCode.encode(K, N, m)
        mt = merkleTree(broadcast_stripes)  # full binary tree
        roothash = mt[1]

        
        for i in range(N):
            branch = getMerkleBranch(i, mt)
            send(target_id = i, message = ('VAL', roothash, branch, broadcast_stripes[i], i), j = query_index)
        logger.debug("{} finish leader send.".format(pid))

    while True: # main receive loop
        sender, message = receive(query_index)  
        if message[0] == 'VAL':
            (message_type, roothash, branch, stripe, hashidx) = message
            if sender != leader:
                logger.warn("{} VAL message from other than leader:{}".format(pid,sender))
                continue
            try:
                assert merkleVerify(N, stripe, roothash, branch, hashidx)
            except Exception as e:
                logger.error("{} Failed to validate VAL message:{}".format(pid,e))
                continue
            # Update
            broadcast((query_index,('ECHO', roothash, branch, stripe)) )

        elif message[0] == 'ECHO':
            logger.debug("{} sid:{} instance:{} receive {}'s rbc ECHO msg".format(pid,sid,query_index,sender)) 
            (message_type, roothash, branch, stripe) = message
            # Validation
            if (roothash in stripes and stripes[roothash][sender] is not None) or sender in echoSenders:
                logger.debug("{} Redundant ECHO".format(pid))
                continue
            try:
                assert merkleVerify(N, stripe, roothash, branch, sender)
            except AssertionError as e:
                logger.error("{} Failed to validate ECHO message with error:{}".format(pid,e))
                continue
            
            # Update
            stripes[roothash][sender] = stripe
            echoSenders.add(sender)
            echoCounter[roothash] += 1
            
            logger.debug("{} rbc instance:{} echoCounter:{} echoSenders:{}")

            if _statisfy_echo_condition(roothash,echoCounter,EchoThreshold,readySent):
                logger.debug("{} broadcast sender:{} instance:{} READY".format(pid,sender,query_index))
                readySent.set()
                broadcast((query_index,('READY', roothash)))

            # Because of network dealy,we may just receive messages when other nodes has already finish READY phase.
            if _statisfy_output_condition(roothash,ready,OutputThreshold,echoCounter,K):
                m = _decode_output(roothash,K,N,stripes)
                return m

        # READY phase
        elif message[0] == 'READY':
            (_, roothash) = message
            # Validation
            if sender in ready[roothash] or sender in readySenders:
                
                continue
            logger.debug("{} receive READY from sender:{} instance:{}".format(pid,sender,query_index))
            
            # Update
            ready[roothash].add(sender)
            readySenders.add(sender)

            # Amplify ready messages
            if _statisfy_ready_condition(roothash,ready,ReadyThreshold,readySent):
                logger.debug("{} broadcast instance:{} READY".format(pid,query_index))
                readySent.set()
                broadcast((query_index, ('READY', roothash)))

            logger.debug("{} ECHO counter threshold:{} received:{} ".format(pid, K, echoCounter[roothash]))
            if _statisfy_output_condition(roothash,ready,OutputThreshold,echoCounter,K):
                m = _decode_output(roothash,K,N,stripes)
                return m