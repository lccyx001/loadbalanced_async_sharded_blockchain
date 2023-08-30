import zerorpc
import logging
from collections import defaultdict
from exceptions import RedundantMessageError, AbandonedNodeError,InvalidArgsError
from gevent.event import Event
from gevent.queue import Queue

logger = logging.getLogger(__name__)
logging.basicConfig(level=logging.INFO,filename="log.log")



class Binaryagreement(object):
    
    def __init__(self,session_id,local_id,N,f,
                 coin_rpc,
                 broadcast_channels,) -> None:
        """
        :param session_id: session identifier
        :param local_id: my id number
        :param N: the number of parties
        :param f: the number of byzantine parties
        :param coin_rpc:common coin rpc server address string
        :param broadcast_channels: broadcast channel host address strings
        :return: blocks until
        """
        self.session_id = session_id
        self.local_id = local_id
        self.N = N
        self.f = f
        self.broadcast_channels = broadcast_channels
        self.remote_channel = [] # lazy load
        self.coin_rpc = coin_rpc
        self.coin_client = None # lazy connect
        
        # Messages received are routed to either a shared coin, the broadcast, or AUX
        # used in first EST phase
        self._reset()

        # This event is triggered whenever bin_values or aux_values changes
        self.bv_signal = Event()


    def run_forever(self,host,port):
        """
        :param host: binaryagreement server host
        :param port: binaryagreement server port
        :return: 
        """
        self.host = host
        self.port = port
        server = zerorpc.Server(self)
        address = "tcp://{}:{}".format(host,port)
        server.bind(address)
        logger.info("starting binaryagreement server :{}".format(self.local_id))
        server.run()

    def init_connections(self):
        self._connect_coin_rpc()
        self._connect_broadcast_channel()
    
    def _coin(self, round):
        if not self.coin_client:
            self._connect_coin_rpc()
        logger.info("local node:{} waiting for common coin in round:{}".format(self.local_id,round))

        while True:
            coin = self.coin_client.get_coin(round)
            if coin is not None:
                return coin

    def _connect_coin_rpc(self,):
        if not self.coin_client:
            client = zerorpc.Client()
            client.connect(self.coin_rpc)
            self.coin_client = client
            logger.info("connect to coin rpc:{}".format(self.coin_rpc))
    
    def _connect_broadcast_channel(self):
        if not self.remote_channel:
            for channel in self.broadcast_channels:
                client = zerorpc.Client()
                client.connect(channel)   
                self.remote_channel.append((channel,client))
        logger.info("local node:{}:{} connect broadcast channels:{}".format(self.host,self.port,self.broadcast_channels))

    def _broadcast(self,message):
        for (channel,client) in self.remote_channel:
            try:
                logger.info("local_id:{} broad cast message: {} to {}".format(self.local_id,message,channel))
                flag = client.receive(self.local_id,(message[0],message[1],message[2]))
                if not flag:
                    logger.error("local_id:{} ,remote failed with {} message:{}".format(self.local_id,channel,message))
            #TODO:except remote error
            except InvalidArgsError:
                logger.error("local_id:{} ,failed because invalid args:{} remote:{}".format(self.local_id,message[2],channel))

    def _reset(self,):

        self.est_values = defaultdict(lambda: [set(), set()]) 
        self.est_sent = defaultdict(lambda: [False, False]) # est_send= {round:[bin_val,its values is True or False][sent or not ]}
        self.aux_values = defaultdict(lambda: [set(), set()]) # used in second AUX phase
        self.conf_values = defaultdict(lambda: {(0,): set(), (1,): set(), (0, 1): set()}) # used in third CONF phase
        self.conf_sent = defaultdict(lambda: {(0,): False, (1,): False, (0, 1): False}) # {round:}
        self.bin_values = defaultdict(set) # bin_values {round:set()} set() value is 0 or 1

    def binaryagreement(self,vi:int):
        """
        :param vi:  1 or 0
        :return: 
        """
        if vi not in (0,1):
            logger.error("invalid vi:{}".format(vi))
            raise InvalidArgsError
        est = vi 

        r = 0
        already_decided = None
        while True:
            logger.info('Node {} Starting with est = {} in epoch {}'.format(self.local_id,est,r))
            
            if not self.est_sent[r][est]:
                self.est_sent[r][est] = True
                self._broadcast(("EST",r,est))

            logger.info("Node {} finish EST broadcast,est={} epoch={}".format(self.local_id,est,r))
            # 循环等待bin_values[r]的值改变,当收到2f+1个节点的est时值会改变
            while len(self.bin_values[r]) == 0:
                # Block until a value is output
                # 这里需要一个bv_signal唤醒程序继续执行，bv_signal信号当收到2f+1个节点的est时值会改变
                logger.info("Node{} waiting for EST phase's value".format(self.local_id))
                self.bv_signal.clear()
                self.bv_signal.wait()

            logger.info("node {} finish EST phase".format(self.local_id))
            # broadcast AUX message, need receive at least 2f+1 est message
            w = next(iter(self.bin_values[r]))  # take an element
            logger.info("node {} broadcast AUX message: {}".format(self.local_id,('AUX', r, w)))
            self._broadcast(('AUX', r, w))

            values = None
            while True:
                logger.info("node {}:AUX phase round:{} bin_values:{} aux_values:{}".format(self.local_id,r,self.bin_values[r],self.aux_values[r]))
                
                # Block until at least N-f AUX values are received
                if 1 in self.bin_values[r] and len(self.aux_values[r][1]) >= self.N - self.f:
                    values = set((1,))
                    # print('[sid:%s] [pid:%d] VALUES 1 %d' % (sid, pid, r))
                    break
                if 0 in self.bin_values[r] and len(self.aux_values[r][0]) >= self.N - self.f:
                    values = set((0,))
                    # print('[sid:%s] [pid:%d] VALUES 0 %d' % (sid, pid, r))
                    break
                if sum(len(self.aux_values[r][v]) for v in self.bin_values[r]) >= self.N - self.f:
                    values = set((0, 1))
                    # print('[sid:%s] [pid:%d] VALUES BOTH %d' % (sid, pid, r))
                    break
                # 等待 n-f 个AUX消息
                self.bv_signal.clear()
                self.bv_signal.wait()
            logger.info('node:{} finish AUX phase with values = {}'.format(self.local_id, values))

            # CONF phase
            # logger.debug(
            #     f'block until at least N-f ({N-f}) CONF values are received',
            #     extra={'nodeid': pid, 'epoch': r})
            logger.info('node:{} start CONF phase,block until at least N-f({}) CONF values are received'.format(self.local_id,self.N-self.f))
            if not self.conf_sent[r][tuple(values)]:
                values = self._wait_for_conf_values(epoch=r,values=values,)
            
            logger.info('node:{} finish CONF phase with values = {}'.format(self.local_id, values))
            
            logger.info('Block until receiving the common coin value')
            # Block until receiving the common coin value
            s = self._coin(r)

            try:
                decide, est, already_decided = self._set_new_estimate(
                    values=values,
                    s=s,
                    already_decided=already_decided,
                )
                if decide: 
                    self._reset()
                    self.bv_signal.clear()
                    return est
            except AbandonedNodeError:
                
                return

            r += 1

    def _set_new_estimate(self,values, s, already_decided):
        decide = False
        if len(values) == 1:
            v = next(iter(values))
            if v == s:
                if already_decided is None:
                    already_decided = v
                    decide = True
                elif already_decided == v:
                    # Here corresponds to a proof that if one party
                    # decides at round r, then in all the following
                    # rounds, everybody will propose r as an
                    # estimation. (Lemma 2, Lemma 1) An abandoned
                    # party is a party who has decided but no enough
                    # peers to help him end the loop.  Lemma: # of
                    # abandoned party <= t
                    raise AbandonedNodeError
            est = v
        else:
            est = s
        return decide, est, already_decided

    def _handle_conf_messages(self,sender, message):
        _, r, v = message
        v = tuple(v)
        if v not in ((0,), (1,), (0, 1)):
            raise InvalidArgsError
        if sender in self.conf_values[r][v]:
            # logger.warn(f'Redundant CONF received {message} by {sender}',
            #             extra={'nodeid': pid, 'epoch': r})
            # FIXME: Raise for now to simplify things & be consistent
            # with how other TAGs are handled. Will replace the raise
            # with a continue statement as part of
            # https://github.com/initc3/HoneyBadgerBFT-Python/issues/10
            raise RedundantMessageError(
                'Redundant CONF received {}'.format(message))

        self.conf_values[r][v].add(sender)
        # logger.debug(
        #     f'add v = {v} to conf_value[{r}] = {conf_values[r]}',
        #     extra={'nodeid': pid, 'epoch': r},
        # )

        self.bv_signal.set()

    def _wait_for_conf_values(self, epoch,values, ):
        self.conf_sent[epoch][tuple(values)] = True
        logger.info("node:{} send CONF message:{}".format(self.local_id,('CONF', epoch, tuple(self.bin_values[epoch]))))
        
        self._broadcast(('CONF', epoch, tuple(self.bin_values[epoch])))
        while True:
            logger.info("node:{} looping CONF phase, conf_values{}".format(self.local_id,self.conf_values[epoch]))
            if 1 in self.bin_values[epoch] and len(self.conf_values[epoch][(1,)]) >= self.N - self.f:
                return set((1,))
            if 0 in self.bin_values[epoch] and len(self.conf_values[epoch][(0,)]) >= self.N - self.f:
                return set((0,))
            if (sum(len(senders) for conf_value, senders in
                    self.conf_values[epoch].items() if senders and
                    set(conf_value).issubset(self.bin_values[epoch])) >= self.N - self.f):
                return set((0, 1))

            self.bv_signal.clear()
            self.bv_signal.wait()

    def receive(self,sender,msg):
        logger.info("local node:{} epoch:{}  receive message:{} from node:{}".format(self.local_id,msg[1],msg,sender))
        if sender not in range(self.N):
            logger.error("sender: {} not in N:{}".format(sender,self.N))
            return
        
        msg_type, round, est_value = msg
        
        if msg[0] == 'EST':
            if est_value not in (0,1):
                raise InvalidArgsError
            # BV_Broadcast message
            if sender in self.est_values[round][est_value]:
                # 重复收到一方发来的信息, 或者是自身发送过的消息
                # FIXME: raise or continue? For now will raise just
                # because it appeared first, but maybe the protocol simply
                # needs to continue.
                # print(f'Redundant EST received by {sender}', msg)
                # logger.warn(
                #     f'Redundant EST message received by {sender}: {msg}',
                #     extra={'nodeid': pid, 'epoch': msg[1]}
                # )
                raise RedundantMessageError(
                    'Redundant EST received {}'.format(msg))
                # continue

            self.est_values[round][est_value].add(sender)
            logger.info("node:{} Round:{} receive EST message:{} sender:{}".format(self.local_id,round,est_value,sender))
            # Relay after reaching first threshold
            # more than f + 1 BA nodes have received round round's EST message，means this message is free fault crash, just broadcast it.
            logger.info("node:{} Round:{}  sender:{} threhold:{}".format(self.local_id,round,sender,len(self.est_values[round][est_value])))
            if len(self.est_values[round][est_value]) >= self.f + 1 and not self.est_sent[round][est_value]:
                self.est_sent[round][est_value] = True
                self._broadcast(('EST', round, est_value))
                logger.info("Round:{} EST Message reached f+1,value is: {}".format(round,est_value))

            # Output after reaching second threshold
            # more than f + 1 BA nodes have received round round's EST message，means this message is free byzantine crash, just broadcast it.
            if len(self.est_values[round][est_value]) >= 2 * self.f + 1:
                logger.info("Round:{} EST Message reached 2f+1,value is:{}".format(round,est_value))
                self.bin_values[round].add(est_value)
                self.bv_signal.set()
            
            return True

        elif msg[0] == 'AUX':
            # AUX message
            if est_value not in (0,1):
                raise InvalidArgsError
            if sender in self.aux_values[round][est_value]:
                # 本节点已经发送过，不需要再次发送
                # FIXME: raise or continue? For now will raise just
                # because it appeared first, but maybe the protocol simply
                # needs to continue.
                # print('Redundant AUX received', msg)
                raise RedundantMessageError(
                    'Redundant AUX received {}'.format(msg))

            # logger.debug(
            #     f'add sender = {sender} to aux_value[{r}][{v}] = {aux_values[r][v]}',
            #     extra={'nodeid': pid, 'epoch': r},
            # )
            self.aux_values[round][est_value].add(sender)
            self.bv_signal.set()
            return True
            
        elif msg[0] == 'CONF':
            self._handle_conf_messages(
                sender=sender,
                message=msg,
            )
