from rpcbase import RPCBase
from enum import Enum
from collections import namedtuple
import logging
from gevent.event import Event
from gevent.queue import Queue
from commoncoin import commoncoin
from binaryagreement import Binaryagreement
from config import Config
import gevent

logger = logging.getLogger(__name__)
logging.basicConfig(level=logging.INFO,filename="log.log")

class BroadcastTag(Enum):
    ACS_COIN = 'ACS_COIN'
    ACS_RBC = 'ACS_RBC'
    ACS_ABA = 'ACS_ABA'
    TPKE = 'TPKE'

class HoneyBadgerBFT(RPCBase):
    """HoneyBadgerBFT object used to run the protocol.

    :param str sid: The base name of the common coin that will be used to
        derive a nonce to uniquely identify the coin.
    :param int pid: Node id.
    :param int B: Batch size of transactions.
    :param int N: Number of nodes in the network.
    :param int f: Number of faulty nodes that can be tolerated.
    :param str sPK: Public key of the threshold signature
        (:math:`\mathsf{TSIG}`) scheme.
    :param str sSK: Signing key of the threshold signature
        (:math:`\mathsf{TSIG}`) scheme.
    :param str ePK: Public key of the threshold encryption
        (:math:`\mathsf{TPKE}`) scheme.
    :param str eSK: Signing key of the threshold encryption
        (:math:`\mathsf{TPKE}`) scheme.
    :param send: gevent.queue.Queue.put_nowait
    :param recv: gevent.queue.Queue.get_nowait
    """

    def __init__(self,sid, pid, B, N, f, sPK, sSK, ePK, eSK, send, recv) -> None:
        self.sid = sid
        self.pid = pid
        self.B = B
        self.N = N
        self.f = f
        self.sPK = sPK
        self.sSK = sSK
        self.ePK = ePK
        self.eSK = eSK
        self._send = send
        self._recv = recv

        self.round = 0  # Current block number
        self.transaction_buffer = []
        self._per_round_recv = {}  # Buffer of each round incoming messages
        self.greenlets = []


    def submit_tx(self,tx):
        logger.info("node:{} submit tx:{}".format(self.pid,tx))
        self.transaction_buffer.append(tx)

    def recv(self, message):
        """Receive messages."""
        if len(message) != 2:
            logger.info("Invalid message:{}".format(message))
            return False
        
        (sender, (r, msg)) = message
        if r < self.round:
            logger.info("Expired message round now:{} message r:{}".format(self.round,r))    
            return False

        # Maintain an *unbounded* recv queue for each epoch
        if r not in self._per_round_recv:
            # Buffer this message
            self._per_round_recv[r] = Queue()

        _recv = self._per_round_recv[r]
        if _recv is not None:
            # Queue it
            _recv.put((sender, msg))
        

    def send(self,):
        pass
        

    # def honeybadgerbft(self):
    #     """Run the HoneyBadgerBFT protocol."""
    #     r = self.round
    #     if r not in self._per_round_recv:
    #         self._per_round_recv[r] = Queue()

    #     # Select all the transactions (TODO: actual random selection)
    #     tx_to_send = self.transaction_buffer[:self.B]

    #     # TODO: Wait a bit if transaction buffer is not full


    #     # Run the round
    #     new_tx = self._one_round(r, tx_to_send[0], send_r, recv_r)
    #     logger.info("new_tx:{}".format(new_tx))

    #     # Remove all of the new transactions from the buffer
    #     self.transaction_buffer = [_tx for _tx in self.transaction_buffer if _tx not in new_tx]

    #     self.round += 1     # Increment the round
    #     if self.round >= 3:
    #         logger.info("Only run one round for now")
    #         return False
    
    def _setup(self):
        self._setup_commoncoin()
        self._setup_aba()
        self._setup_rbc()
        pass

    def _setup_commoncoin(self,):
        cfg = Config(self.pid) #TODO
        cc = commoncoin(self.sid + 'COIN' + str(j),self.pid,cfg.N,cfg.f,cfg.PK,cfg.SK,cfg.cc_channels,cfg.cc_host,cfg.cc_port)
        ccgl = gevent.spawn(cc.run_forever())
        self.greenlets.append(ccgl) 
        logger.info("set up common coin")

    def _setup_aba(self):
        cfg = Config(self.pid) #TODO
        aba = Binaryagreement()
        pass

    def _setup_rbc(self):
        pass

    # def _one_round(self, r, tx_to_send, send, recv):
    #     """Run one protocol round.

    #     :param int r: round id
    #     :param tx_to_send: Transaction(s) to process.
    #     :param send:
    #     :param recv:
    #     """
    #     # Unique sid for each round
    #     sid = self.sid + ':' + str(r)
    #     pid = self.pid
    #     N = self.N
    #     f = self.f

    #     def broadcast(o):
    #         """Multicast the given input ``o``.

    #         :param o: Input to multicast.
    #         """
    #         for j in range(N):
    #             send(j, o)

    #     # Launch ACS, ABA, instances
    #     coin_recvs = [None] * N
    #     aba_recvs  = [None] * N  # noqa: E221
    #     rbc_recvs  = [None] * N  # noqa: E221

    #     aba_inputs  = [Queue(1) for _ in range(N)]  # noqa: E221
    #     aba_outputs = [Queue(1) for _ in range(N)]
    #     rbc_outputs = [Queue(1) for _ in range(N)]

    #     my_rbc_input = Queue(1)
    #     print(pid, r, 'tx_to_send:', tx_to_send)

    #     def _setup(j):
    #         """Setup the sub protocols RBC, BA and common coin.

    #         :param int j: Node index for which the setup is being done.
    #         """
    #         def coin_bcast(o):
    #             """Common coin multicast operation.

    #             :param o: Value to multicast.
    #             """
    #             broadcast(('ACS_COIN', j, o))

    #         coin_recvs[j] = Queue()
    #         coin = shared_coin(sid + 'COIN' + str(j), pid, N, f,
    #                            self.sPK, self.sSK,
    #                            coin_bcast, coin_recvs[j].get)

    #         def aba_bcast(o):
    #             """Binary Byzantine Agreement multicast operation.

    #             :param o: Value to multicast.
    #             """
    #             broadcast(('ACS_ABA', j, o))

    #         aba_recvs[j] = Queue()
    #         gevent.spawn(binaryagreement, sid+'ABA'+str(j), pid, N, f, coin,
    #                      aba_inputs[j].get, aba_outputs[j].put_nowait,
    #                      aba_bcast, aba_recvs[j].get)

    #         def rbc_send(k, o):
    #             """Reliable broadcast operation.

    #             :param o: Value to broadcast.
    #             """
    #             send(k, ('ACS_RBC', j, o))

    #         # Only leader gets input
    #         rbc_input = my_rbc_input.get if j == pid else None
    #         rbc_recvs[j] = Queue()
    #         rbc = gevent.spawn(reliablebroadcast, sid+'RBC'+str(j), pid, N, f, j,
    #                            rbc_input, rbc_recvs[j].get, rbc_send)
    #         rbc_outputs[j] = rbc.get  # block for output from rbc

    #     # N instances of ABA, RBC
    #     for j in range(N):
    #         _setup(j)

    #     # One instance of TPKE
    #     def tpke_bcast(o):
    #         """Threshold encryption broadcast."""
    #         broadcast(('TPKE', 0, o))

    #     tpke_recv = Queue()

    #     # One instance of ACS
    #     acs = gevent.spawn(commonsubset, pid, N, f, rbc_outputs,
    #                        [_.put_nowait for _ in aba_inputs],
    #                        [_.get for _ in aba_outputs])

    #     recv_queues = BroadcastReceiverQueues(
    #         ACS_COIN=coin_recvs,
    #         ACS_ABA=aba_recvs,
    #         ACS_RBC=rbc_recvs,
    #         TPKE=tpke_recv,
    #     )
    #     gevent.spawn(broadcast_receiver_loop, recv, recv_queues)

    #     _input = Queue(1)
    #     _input.put(tx_to_send)
    #     return honeybadger_block(pid, self.N, self.f, self.ePK, self.eSK,
    #                              _input.get,
    #                              acs_in=my_rbc_input.put_nowait, acs_out=acs.get,
    #                              tpke_bcast=tpke_bcast, tpke_recv=tpke_recv.get)

def _setup_commoncoin():
    from config import Config
    
    for i in range(4):
        cfg = Config(i)
        cc = commoncoin("test",,cfg.N,cfg.f,cfg.PK,cfg.SK,cfg.cc_channels,cfg.cc_host,cfg.cc_port)
        print(vars(cc))
    


if __name__ == "__main__":
    _setup_commoncoin()
    pass