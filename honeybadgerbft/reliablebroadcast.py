# coding=utf-8
from collections import defaultdict
from loadbalanced_async_sharded_blockchain.honeybadgerbft.utils import ErasureCode,merkleTree,getMerkleBranch,merkleVerify
import logging
import zerorpc
from loadbalanced_async_sharded_blockchain.honeybadgerbft.exceptions import WrongTypeError
from gevent.event import Event
from loadbalanced_async_sharded_blockchain.honeybadgerbft.clientbase import ClientBase

logger = logging.getLogger(__name__)
logging.basicConfig(level=logging.INFO,filename="log.log")


def reliablebroadcast(sid, pid, N, f, leader, rpcbase:ClientBase,j):
    """Reliable broadcast

    :param int pid: ``0 <= pid < N``
    :param int N:  at least 3
    :param int f: fault tolerance, ``N >= 3f + 1``
    :param int leader: ``0 <= leader < N``
    :param input: if ``pid == leader``, then :func:`input()` is called
        to wait for the input value
    
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
    def _decode_output(roothash):
        # Rebuild the merkle tree to guarantee decoding is correct
        m = ErasureCode.decode(K, N, stripes[roothash])
        _stripes = ErasureCode.encode(K, N, m)
        _mt = merkleTree(_stripes)
        _roothash = _mt[1]
        # TODO: Accountability: If this fails, incriminate leader
        assert _roothash == roothash
        return m
    
    def _statisfy_echo_condition(echoCounter,roothash,EchoThreshold,readySent):
        return echoCounter[roothash] >= EchoThreshold and not readySent
    
    def _statisfy_output_condition(ready,roothash,OutputThreshold,echoCounter,K):
        return len(ready[roothash]) >= OutputThreshold and echoCounter[roothash] >= K
    
    def _statisfy_ready_condition(ready,roothash,ReadyThreshold,readySent):
        return len(ready[roothash]) >= ReadyThreshold and not readySent
    
    def _handle_VAL_message(sender, message):
        # Validation
        logger.debug("{} receive VAL message from:{}".format(pid,sender))
        (message_type, roothash, branch, stripe, hashidx) = message
        if sender != leader:
            logger.warn("{} VAL message from other than leader:{}".format(pid,sender))
            return
        try:
            assert merkleVerify(N, stripe, roothash, branch, hashidx)
        except Exception as e:
            logger.error("{} Failed to validate VAL message:{}".format(pid,e))
            return
        
        # Update
        logger.debug("{} receive {}'s VAL message.".format(pid,sender))
        broadcast((j,('ECHO', roothash, branch, stripe)) )
        
    
    def _handle_ECHO_message(sender, message,readySent):
        (message_type, roothash, branch, stripe) = message
        # Validation
        if (roothash in stripes and stripes[roothash][sender] is not None) or sender in echoSenders:
            logger.debug("{} Redundant ECHO".format(pid))
            return
        
        try:
            assert merkleVerify(N, stripe, roothash, branch, sender)
        except AssertionError as e:
            logger.error("{} Failed to validate ECHO message with error:{}".format(pid,e))
            return

        logger.debug("{} receive ECHO from sender:{} instance:{}".format(pid,sender,j))
        # Update
        stripes[roothash][sender] = stripe
        echoSenders.add(sender)
        echoCounter[roothash] += 1
        
        if _statisfy_echo_condition(echoCounter,roothash,EchoThreshold,readySent):
            logger.debug("{} broadcast sender:{} instance:{} READY".format(pid,sender,j))
            readySent = True
            broadcast((j,('READY', roothash)))

        # Because of network dealy,we may just receive messages when other nodes has already finish READY phase.
        if _statisfy_output_condition(ready,roothash,OutputThreshold,echoCounter,K):
            m = _decode_output(roothash)
            rbc_in(m,j)
            logger.debug("{}:{} finish RBC and decode output".format(pid,j))
            return m
        
    def _handle_READY_message(sender,message,readySent):
        (_, roothash) = message
        
        # Validation
        if sender in ready[roothash] or sender in readySenders:
            logger.warn("{} Redundant READY from {}".format(pid,sender))
            return
        
        logger.debug("{} receive READY from sender:{} instance:{}".format(pid,sender,j))
        # Update
        ready[roothash].add(sender)
        readySenders.add(sender)

        # Amplify ready messages
        if _statisfy_ready_condition(ready,roothash,ReadyThreshold,readySent):
            logger.debug("{} broadcast instance:{} READY".format(pid,j))
            readySent = True
            #TODO:check if pid is right
            broadcast((pid, ('READY', roothash)))

        logger.debug("{} ECHO counter threshold:{} received:{} ".format(pid, K, echoCounter[roothash]))
        if _statisfy_output_condition(ready,roothash,OutputThreshold,echoCounter,K):
            m = _decode_output(roothash)
            rbc_in(m,j)
            logger.debug("{}:{} finish RBC and decode output".format(pid,j))
            return m


    input = rpcbase.input_rbc if pid == leader else None
    receive = rpcbase.receive_rbc
    send = rpcbase.send_rbc
    broadcast = rpcbase.broadcast_rbc
    rbc_in = rpcbase.rbc_in

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
    if pid == leader:
        # The leader erasure encodes the input, sending one strip to each participant
        m = input()  # block until an input is received
        if not isinstance(m, (str, bytes)):
            raise WrongTypeError("m must be str or bytes type")
        logger.info("{} received {} bytes ".format(pid,len(m)))

        stripes = ErasureCode.encode(K, N, m)
        mt = merkleTree(stripes)  # full binary tree
        roothash = mt[1]
        logger.debug("{} make stripes tree:{}".format(pid,mt))

        logger.debug("{} as leader send branch".format(pid))
        for i in range(N):
            branch = getMerkleBranch(i, mt)
            logger.debug("{} leader send to {} VAL".format(pid,i))
            send(i, ('VAL', roothash, branch, stripes[i], i), j)
            logger.debug("{} leader send to {} finish".format(pid,i))
        logger.info("{} finish leader send phase".format(pid))
    # TODO: filter policy: if leader, discard all messages until sending VAL

    fromLeader = None
    stripes = defaultdict(lambda: [None for _ in range(N)])
    echoCounter = defaultdict(lambda: 0)
    echoSenders = set()  # Peers that have sent us ECHO messages
    ready = defaultdict(set)
    readySent = False
    readySenders = set()  # Peers that have sent us READY messages

    while True: # main receive loop
        sender, message = receive(j)   
        
        if message[0] == 'VAL' and fromLeader is None:
            # validate val message and broadcast ECHO message.
            _handle_VAL_message(sender=sender,message=message)

        # ECHO phase check Merkle branch, if receive from N-f distinct nodes and not send READY message than broadcast READY to other nodes.
        elif message[0] == 'ECHO':
            finsh_ready = _handle_ECHO_message(sender=sender,message=message,readySent=readySent)
            if finsh_ready:
                return finsh_ready
            
        # READY phase
        elif message[0] == 'READY':
            finsh_ready = _handle_READY_message(sender=sender,message=message,readySent=readySent)
            if finsh_ready:
                return finsh_ready
            
