# coding=utf-8
from collections import defaultdict
from utils import ErasureCode,merkleTree,getMerkleBranch,merkleVerify
import logging
import zerorpc
from exceptions import WrongTypeError
from gevent.event import Event
from rpcbase import RPCBase

logger = logging.getLogger(__name__)
logging.basicConfig(level=logging.INFO,filename="log.log")


def reliablebroadcast(sid, pid, N, f, leader, input:RPCBase.input_rbc, receive:RPCBase.receive_rbc, send:RPCBase.send_rbc,broadcast:RPCBase.broadcast_rbc,rbc_in:RPCBase.rbc_in,j):
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

        logger.info("{} as leader send branch".format(pid))
        for i in range(N):
            branch = getMerkleBranch(i, mt)
            logger.info("{} leader send to {} VAL".format(pid,i))
            send(i, ('VAL', roothash, branch, stripes[i], i), j)
            logger.info("{} leader send to {} finish".format(pid,i))

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
        logger.info("{}:{} receive from {} message:{}".format(pid,j,sender,message))
        if message[0] == 'VAL' and fromLeader is None:
            # Validation
            logger.info("{} receive VAL message from:{}".format(pid,sender))
            (message_type, roothash, branch, stripe, hashidx) = message
            if sender != leader:
                logger.info("{} VAL message from other than leader:{}".format(pid,sender))
                continue
            try:
                assert merkleVerify(N, stripe, roothash, branch, hashidx)
            except Exception as e:
                logger.error("{} Failed to validate VAL message:{}".format(pid,e))
                continue
            
            # Update
            logger.info("{} make VAL phase broadcast.".format(pid,))
            broadcast((j,('ECHO', roothash, branch, stripe)) )

        # ECHO phase check Merkle branch, if receive from N-f distinct nodes and not send READY message than broadcast READY to other nodes.
        elif message[0] == 'ECHO':
            (message_type, roothash, branch, stripe) = message
            # Validation
            logger.info("{} receive ECHO message from:{}".format(pid,sender))
            if (roothash in stripes and stripes[roothash][sender] is not None) or sender in echoSenders:
                logger.info("{} Redundant ECHO".format(pid))
                continue
            
            try:
                assert merkleVerify(N, stripe, roothash, branch, sender)
            except AssertionError as e:
                logger.error("{} Failed to validate ECHO message with error:{}".format(pid,e))
                continue

            logger.info("{} finish check ECHO message".format(pid))
            
            # Update
            stripes[roothash][sender] = stripe
            echoSenders.add(sender)
            echoCounter[roothash] += 1

            logger.info("{} ECHO phase update state,from sender:{}  echoSenders:{} echoCounter:{}".format(
                pid,
                sender,
                echoSenders,
                echoCounter))
            
            if echoCounter[roothash] >= EchoThreshold and not readySent:
                logger.info("{} statisfy echo threshold and not send ready, now broadcast READY in ECHO phase".format(pid))
                readySent = True
                broadcast((j,('READY', roothash)))

            # Because of network dealy,we may just receive messages when other nodes has already finish READY phase.
            if len(ready[roothash]) >= OutputThreshold and echoCounter[roothash] >= K:
                m = _decode_output(roothash)
                rbc_in(m,j)
                logger.info("{} in ECHO phase finish RBC and decode output{}".format(pid,m))
                return m
        
        # READY phase
        elif message[0] == 'READY':
            (_, roothash) = message
            logger.info("{} receive READY message from:{}".format(pid,sender))
            
            # Validation
            if sender in ready[roothash] or sender in readySenders:
                logger.info("{} Redundant READY".format(pid))
                continue

            # Update
            ready[roothash].add(sender)
            readySenders.add(sender)
            logger.info("{} READY threshold:{} received:{} ".format(pid,ReadyThreshold,ready[roothash]))

            # Amplify ready messages
            if len(ready[roothash]) >= ReadyThreshold and not readySent:
                logger.info("{} statisfy READY threshold and not send ready, now broadcast READY in READY phase".format(pid,))
                readySent = True
                broadcast((pid, ('READY', roothash)))

            logger.info("{} ECHO counter threshold:{} received:{} ".format(pid, K, echoCounter[roothash]))
            if len(ready[roothash]) >= OutputThreshold and echoCounter[roothash] >= K:
                m = _decode_output(roothash)
                rbc_in(m,j)
                logger.info("{} finish RBC and decode output:{}".format(pid,m))
                return m
