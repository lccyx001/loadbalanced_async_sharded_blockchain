import logging
from commoncoin import commoncoin
from binaryagreement import binaryagreement
from commonsubset import commonsubset
from reliablebroadcast import reliablebroadcast
from honeybadger_block import honeybadger_block

import gevent


logger = logging.getLogger(__name__)
logging.basicConfig(level=logging.INFO,filename="log.log")

class HoneyBadgerBFT(object):
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

    def __init__(self,sid, pid, B, N, f, sPK, sSK, ePK, eSK, rpcbase) -> None:
        self.sid = sid
        self.pid = pid
        self.B = B
        self.N = N
        self.f = f
        self.sPK = sPK
        self.sSK = sSK
        self.ePK = ePK
        self.eSK = eSK

        self.round = 0  # Current block number
        self.transaction_buffer = []
        self._per_round_recv = {}  # Buffer of each round incoming messages
        
        self._recv_thread = None
        self._client = rpcbase


    def submit_tx(self,tx):
        logger.info("{} submit tx:{}".format(self.pid,tx))
        self.transaction_buffer.append(tx)

    def run(self):
        """Run the HoneyBadgerBFT protocol."""

        # while True:
            # For each round...
        r = self.round

        # Select all the transactions (TODO: actual random selection)
        tx_to_send = self.transaction_buffer[:self.B]

        # TODO: Wait a bit if transaction buffer is not full
        new_tx = self._run_round(r, tx_to_send[0])
        logger.info('{} new_tx:{}'.format(self.pid,new_tx))

        # Remove all of the new transactions from the buffer
        self.transaction_buffer = [_tx for _tx in self.transaction_buffer if _tx not in new_tx]
        self.round += 1     # Increment the round
        self._client.reset()
        logger.info("{} rpc reset".format(self.pid))

    
    def _run_round(self, r, tx_to_send):
        """Run one protocol round.

        :param int r: round id
        :param tx_to_send: Transaction(s) to process.
        """
        def _setup(j):
            """Setup the sub protocols RBC, BA and common coin.

            :param int j: Node index for which the setup is being done.
            """
            cc_sid = sid + 'COIN' + str(j)
            coin = commoncoin(cc_sid, pid, N, f,self.sPK, self.sSK,self._client,j)
            logger.debug("init {} commoncoin instance".format(j))

            aba_sid = sid+'ABA'+str(j)
            gevent.spawn(binaryagreement, aba_sid, pid, N, f, coin,self._client,j)
            logger.debug("init {} binaryagreement instance".format(j))

            # Only leader gets input
            rbc_input = self._client.input_rbc if j == pid else None
            rbc_sid = sid+'RBC'+str(j)
            gevent.spawn(reliablebroadcast, rbc_sid , pid, N, f, j,rbc_input, self._client,j)
            logger.debug("init {} reliablebroadcast instance".format(j))

        # Unique sid for each round
        sid = self.sid + ':' + str(r)
        pid = self.pid
        N = self.N
        f = self.f

        # N instances of ABA, RBC
        for j in range(N):
            _setup(j)
            
        # One instance of ACS
        acs = gevent.spawn(commonsubset, pid, N, f, self._client.rbc_out,self._client.aba_in,self._client.aba_out)
        logger.info("{} round {} setup finish".format(pid,r))

        self._client.propose_set(tx_to_send)
        return honeybadger_block(pid, self.N, self.f, self.ePK, self.eSK,acs_out=acs.get,rpcbase= self._client)