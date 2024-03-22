import logging
from loadbalanced_async_sharded_blockchain.honeybadgerbft.commoncoin import commoncoin
from loadbalanced_async_sharded_blockchain.honeybadgerbft.binaryagreement import binaryagreement
from loadbalanced_async_sharded_blockchain.honeybadgerbft.commonsubset import commonsubset
from loadbalanced_async_sharded_blockchain.honeybadgerbft.reliablebroadcast import reliablebroadcast
from loadbalanced_async_sharded_blockchain.honeybadgerbft.honeybadger_block import honeybadger_block
from loadbalanced_async_sharded_blockchain.common.config import Config
import gevent
import traceback

logger = logging.getLogger(__name__)
logging.basicConfig(level=logging.INFO,filename="log.log")

class HoneyBadgerBFT(object):
    """HoneyBadgerBFT object used to run the protocol.

    :param str sid: common coin会使用这个sid生成身份.
    :param int pid: 节点id.
    :param int N: 网络中节点总数.
    :param int f: 能容忍的拜占庭节点数.
    :param str sPK: 签名算法公钥.
    :param str sSK: 签名算法私钥.
    :param str ePK: 加密算法公钥.
    :param str eSK: 加密算法私钥.
    :param send: gevent.queue.Queue.put_nowait
    :param recv: gevent.queue.Queue.get_nowait
    """
    # TODO:不能连续运行，会出现偶发性错误
    def __init__(self,sid, pid,client) -> None:
        self.sid = sid
        self.pid = pid
        config = Config(pid)

        self._N = config.N
        self._f = config.f
        self._sPK = config.PK
        self._sSK = config.SK
        self._ePK = config.ePK
        self._eSK = config.eSK
        
        self._client = client

        self._round = 0  # Current block number
        self._transaction_json_buffer = None
        self._recv_thread = None

    def submit_txs(self,tx_json):
        """tx_json:transaction strings"""
        assert isinstance(tx_json,str)
        self._transaction_json_buffer = tx_json

    def run(self):
        """Run the HoneyBadgerBFT protocol."""
        r = self._round
        tx_to_send = self._transaction_json_buffer
        try:
            all_gls = []
            new_tx = self._run_round(r, tx_to_send,all_gls)
        except Exception as e:
            traceback.print_exc()
            logger.error(e)
            self._transaction_json_buffer = None
            if not all_gls:
                gevent.killall(all_gls)
            return None
        
        self._round += 1     # Increment the round
        self._transaction_json_buffer = None
        return new_tx

    
    def _run_round(self, r, tx_to_send,all_gls):
        """Run one protocol round.

        :param int r: round id
        :param tx_to_send: Transaction(s) to process.
        """
        def _setup(j):
            """Setup the sub protocols RBC, BA and common coin.

            :param int j: Node index for which the setup is being done.
            """
            cc_sid = sid + 'COIN' + str(j)
            coin,coin_gl = commoncoin(cc_sid, pid, N, f,self._sPK, self._sSK,self._client,j)
            logger.debug("init {} commoncoin instance".format(j))

            aba_sid = sid+'ABA'+str(j)
            ba_gl = gevent.spawn(binaryagreement, aba_sid, pid, N, f, coin,self._client,j)
            logger.debug("init {} binaryagreement instance".format(j))

            # Only leader gets input
            rbc_sid = sid+'RBC'+str(j)
            rbc_gl = gevent.spawn(reliablebroadcast, rbc_sid , pid, N, f, j, self._client,j)
            logger.debug("init {} reliablebroadcast instance".format(j))
            rbc_out.append(rbc_gl.get)
            all_gls.extend([coin_gl,ba_gl,rbc_gl])

        # Unique sid for each round
        sid = self.sid + ':' + str(r)
        pid = self.pid
        N = self._N
        f = self._f
        rbc_out = []
        
        # N instances of ABA, RBC
        for j in range(N):
            _setup(j)
            
        # One instance of ACS
        acs = gevent.spawn(commonsubset, pid, N, f,rbc_out, self._client)
        all_gls.append(acs)
        # logger.info("{} round {} setup finish".format(pid,r))

        self._client.propose_set(tx_to_send)

        return honeybadger_block(pid, self._N, self._f, self._ePK, self._eSK,acs_out=acs.get,rpcbase= self._client)