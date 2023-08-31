# coding=utf-8
from collections import defaultdict
from utils import ErasureCode,merkleTree,getMerkleBranch,merkleVerify
import logging
import zerorpc
from exceptions import WrongTypeError
from gevent.event import Event

logger = logging.getLogger(__name__)
logging.basicConfig(level=logging.INFO,filename="log.log")

class ReliableBroadcast(object):
    
    def __init__(self,sid, pid, N, f, leader, broadcast_channels) -> None:
        """Reliable broadcast
        :param int sid: session id?
        :param int pid: ``0 <= pid < N``
        :param int N: at least 3
        :param int f: fault tolerance, ``N >= 3f + 1``
        :param int leader: ``0 <= leader < N``

        :return None
        call output function to get the RBC result m
        : ``m`` after receiving :math:`2f+1` ``READY`` messages
            and :math:`N-2f` ``ECHO`` messages

            .. important:: **Messages**

                ``VAL( roothash, branch[i], stripe[i] )``
                    sent from ``leader`` to each other party
                ``ECHO( roothash, branch[i], stripe[i] )``
                    sent after receiving ``VAL`` message
                ``READY( roothash )``
                    sent after receiving :math:`N-f` ``ECHO`` messages
                    or after receiving :math:`f+1` ``READY`` messages
        .. todo::
            **Accountability**

            A large computational expense occurs when attempting to
            decode the value from erasure codes, and recomputing to check it
            is formed correctly. By transmitting a signature along with
            ``VAL`` and ``ECHO``, we can ensure that if the value is decoded
            but not necessarily reconstructed, then evidence incriminates
            the leader.

        """
        self.sid = sid
        self.pid = pid
        self.N = N
        self.f = f
        self.leader = leader
        self.broadcast_channels = broadcast_channels
        self.remote_channels = defaultdict(list) # lazy load

        self._validate()

        self.K               = N - 2 * f  # Need this many to reconstruct. (# noqa: E221)
        self.EchoThreshold   = N - f      # Wait for this many ECHO to send READY. (# noqa: E221)
        self.ReadyThreshold  = f + 1      # Wait for this many READY to amplify READY. (# noqa: E221)
        self.OutputThreshold = 2 * f + 1  # Wait for this many READY to output
        # NOTE: The above thresholds  are chosen to minimize the size
        # of the erasure coding stripes, i.e. to maximize K.
        # The following alternative thresholds are more canonical
        # (e.g., in Bracha '86) and require larger stripes, but must wait
        # for fewer nodes to respond
        #   EchoThreshold = ceil((N + f + 1.)/2)
        #   K = EchoThreshold - f
        self._init_RBC_params()

    def _init_RBC_params(self):
        self.fromLeader = None
        self.stripes = defaultdict(lambda: [None for _ in range(self.N)])
        self.echoCounter = defaultdict(lambda: 0)
        self.echoSenders = set()  # Peers that have sent us ECHO messages
        self.ready = defaultdict(set)
        self.readySent = False
        self.readySenders = set()  # Peers that have sent us READY messages
        self.RBCResult = None
        
        
    def _validate(self):
        assert self.N >= 3*self.f + 1
        assert self.f >= 0
        assert 0 <= self.leader < self.N
        assert 0 <= self.pid < self.N

    def _broadcast(self,message):
        for id, (address,client) in self.remote_channels.items():
            logger.info("local node:{} broadcast {} message to id:{} address:{}".format(self.pid,message[0],id,address))
            try:
                flag = client.receive(self.pid,message)
                if not flag:
                    logger.error("local node:{} send {} message to remote:{} failed".format(self.pid,message[0],address))
            except Exception as e:
                logger.info("local node:{} send {} message to remote:{} failed with exception".format(self.pid,message[0],address))
                logger.error(e)

    def _send(self,recipient,message):
        for id, (address,client) in self.remote_channels.items():
            if recipient!=id: 
                continue
            try:
                logger.info("local node:{} send branch to recipient:{}".format(self.pid,recipient))
                flag = client.receive(self.pid,message)
                if not flag:
                    logger.error("local node:{} send {} message to remote:{} failed".format(self.pid,message[0],address))
            except Exception as e:
                logger.info("local node:{} send message:{} to remote:{} failed with exception".format(self.pid,message,address))
                logger.error(e)

    
    def init_connections(self,):
        if not self.remote_channels:
            for (id,channel) in self.broadcast_channels:
                client = zerorpc.Client()
                client.connect(channel)   
                self.remote_channels.update({id:[channel,client]})
        logger.info("local node:{}:{} connect broadcast channels:{}".format(self.host,self.port,self.broadcast_channels))
    
    def reliablebroadcast(self,m):
        # The leader erasure encodes the input, sending one strip to each participant
        # XXX Python 3 related issue, for now let's tolerate both bytes and
        # strings
        # (with Python 2 it used to be: assert type(m) is str)
        if not isinstance(m, (str, bytes)):
            logger.error("local node:{} receive wrong type message:{}".format(self.pid,type(m)))
            raise WrongTypeError("m must be str or bytes type")
        
        # print('Input received: %d bytes' % (len(m),))
        logger.info("local node:{} received {} bytes ".format(self.pid,len(m)))

        stripes = ErasureCode.encode(self.K, self.N, m)
        logger.info("local node:{} erasure coded stripe piceses:{} can restruct with {} piece".format(self.pid,len(stripes),self.K))

        mt = merkleTree(stripes)  # full binary tree
        logger.info("local node:{} making merkle tree length:{}".format(self.pid,len(mt)))
        roothash = mt[1]

        for i in range(self.N):
            logger.info("local node:{} send {}th piece ".format(self.pid,i))
            branch = getMerkleBranch(i, mt)
            if i == self.pid:
                # send strip to self
                self.receive(self.pid,('VAL', roothash, branch, stripes[i]))
            else:
                self._send(i, ('VAL', roothash, branch, stripes[i]))
        return True

    def receive(self,sender,message):
        # VAL phase: receive VAL message from leader and broadcast ECHO message to other nodes
        if message[0] == 'VAL' and self.fromLeader is None:
            # Validation
            logger.info("local node:{} receive VAL message from:{}".format(self.pid,sender))
            (message_type, roothash, branch, stripe) = message
            if sender != self.leader:
                logger.error("local node:{} VAL message from other than leader:{}".format(self.pid,sender))
                return False
            try:
                assert merkleVerify(self.N, stripe, roothash, branch, self.pid)
            except Exception as e:
                logger.error("local node:{} Failed to validate VAL message:{}".format(self.pid,e))
                return False
            
            logger.info("local node:{} VAL message finish check, roothash:{}.".format(self.pid,roothash))
            # Update
            self.fromLeader = roothash

            logger.info("local node:{} make VAL phase broadcast.".format(self.pid,))
            self._broadcast(('ECHO', roothash, branch, stripe))

            logger.info("local node:{} finish VAL phase.".format(self.pid))
            return True
        
        # ECHO phase check Merkle branch, if receive from N-f distinct nodes and not send READY message than broadcast READY to other nodes.
        elif message[0] == 'ECHO':
            (message_type, roothash, branch, stripe) = message
            # Validation
            logger.info("local node:{} receive ECHO message from:{}".format(self.pid,sender))
            if roothash in self.stripes and self.stripes[roothash][sender] is not None \
            or sender in self.echoSenders:
                logger.info("local node:{} Redundant ECHO".format(self.pid))
                return True
            
            logger.info("local node:{} check merkle tree hash".format(self.pid))
            try:
                assert merkleVerify(self.N, stripe, roothash, branch, sender)
            except AssertionError as e:
                logger.error("local node:{} Failed to validate ECHO message with error:{}".format(self.pid,e))
                return False

            logger.info("local node:{} finish check ECHO message".format(self.pid))
            
            # Update
            self.stripes[roothash][sender] = stripe
            self.echoSenders.add(sender)
            self.echoCounter[roothash] += 1
            logger.info("local node:{} ECHO phase update state,from sender:{}  echoSenders:{} echoCounter:{}".format(
                self.pid,
                sender,
                self.echoSenders,
                self.echoCounter))
            
            if self.echoCounter[roothash] >= self.EchoThreshold and not self.readySent:
                logger.info("local node:{} statisfy echo threshold and not send ready, now broadcast READY in ECHO phase".format(self.pid))
                self.readySent = True
                self._broadcast(('READY', roothash))

            # Because of network dealy,we may just receive messages when other nodes has already finish READY phase.
            if len(self.ready[roothash]) >= self.OutputThreshold and self.echoCounter[roothash] >= self.K:
                logger.info("local node:{} in ECHO phase send READY message".format(self.pid))
                self.RBCResult = self._decode_output(roothash)
                return True
            
            return True
        
        # READY phase
        elif message[0] == 'READY':
            (_, roothash) = message
            logger.info("local node:{} receive READY message from:{}".format(self.pid,sender))
            # Validation
            logger.info("local node:{} start READY check".format(self.pid,))
            if sender in self.ready[roothash] or sender in self.readySenders:
                logger.info("local node:{} Redundant READY".format(self.pid))
                return True

            # Update
            self.ready[roothash].add(sender)
            self.readySenders.add(sender)
            logger.info("local node:{} start READY check readySenders:{}, ready:{}".format(self.pid,self.readySenders,self.ready))

            logger.info("local node:{} READY threshold:{} received:{} ".format(self.pid,self.ReadyThreshold,self.ready[roothash]))
            # Amplify ready messages
            if len(self.ready[roothash]) >= self.ReadyThreshold and not self.readySent:
                logger.info("local node:{} statisfy READY threshold and not send ready, now broadcast READY in READY phase".format(self.pid,))
                self.readySent = True
                self._broadcast(('READY', roothash))

            logger.info("local node:{} ECHO counter threshold:{} received:{} ".format(self.pid, self.K, self.echoCounter[roothash]))
            if len(self.ready[roothash]) >= self.OutputThreshold and self.echoCounter[roothash] >= self.K:
                logger.info("local node:{} finish RBC and decode output:{}".format(self.pid,self.RBCResult))
                self.RBCResult = self._decode_output(roothash)
                return True
            return True

    def RBCresult(self,):
        return self.RBCResult

    def _decode_output(self,roothash):
        # Rebuild the merkle tree to guarantee decoding is correct
        m = ErasureCode.decode(self.K, self.N, self.stripes[roothash])
        _stripes = ErasureCode.encode(self.K, self.N, m)
        _mt = merkleTree(_stripes)
        _roothash = _mt[1]
        # TODO: Accountability: If this fails, incriminate leader
        assert _roothash == roothash
        return m

    def run_forever(self,host,port):
        """
        :param host: reliablebroadcast server host
        :param port: reliablebroadcast server port
        :return: 
        """
        self.host = host
        self.port = port
        server = zerorpc.Server(self)
        address = "tcp://{}:{}".format(host,port)
        server.bind(address)
        logger.info("starting reliablebroadcast server :{}".format(self.pid))
        server.run()
    
