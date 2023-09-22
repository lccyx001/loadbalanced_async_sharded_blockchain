import logging
from collections import defaultdict
from loadbalanced_async_sharded_blockchain.honeybadgerbft.exceptions import RedundantMessageError, AbandonedNodeError,InvalidArgsError
import gevent
from gevent.event import Event
from loadbalanced_async_sharded_blockchain.honeybadgerbft.commoncoin import commoncoin
from loadbalanced_async_sharded_blockchain.honeybadgerbft.clientbase import ClientBase

logger = logging.getLogger(__name__)
logging.basicConfig(level=logging.INFO,filename="log.log")

def _make_message(query_index,message_type,epoch_number,content):
    return (query_index,(message_type,epoch_number,content))

def binaryagreement(sid,pid,N,f,coin:commoncoin,rpcbase:ClientBase,query_index):
    """
    :param sid: session identifier
    :param pid: my id number
    :param N: the number of parties
    :param f: the number of byzantine parties
    :param coin:CommonCoin.get_coin
    :param rpcbase: RPCBase
    :param query_index: RPCBase query index

    :return: blocks until
    """
    
    def _not_broadcast_EST_message(est_sent,r,est):
        return not est_sent[r][est]

    def _meet_broadcast_condition(est_values,epoch,est_value,f,est_sent):
        return len(est_values[epoch][est_value]) >= f + 1 and not est_sent[epoch][est_value]

    def _meet_output_condition(est_values,r,est_value,f):
        return len(est_values[r][est_value]) >= 2 * f + 1
    
    def _handle_EST_message(r,sender,est_value,est_values,est_sent,bin_values,bv_signal):
        if est_value not in (0,1):
            raise InvalidArgsError
        # BV_Broadcast message
        if sender in est_values[r][est_value]:
            # FIXME: raise or continue? For now will raise just
            # because it appeared first, but maybe the protocol simply
            # needs to continue.
            
            logger.warn("{} redundant EST received".format(pid))
            # raise RedundantMessageError('Redundant EST received')
            return 

        est_values[r][est_value].add(sender)
        logger.debug("{} Round:{} receive EST message:{} sender:{} threhold:{}".format(pid,r,est_value,sender,len(est_values[r][est_value])))
        
        # Relay after reaching first threshold
        if _meet_broadcast_condition(est_values,r,est_value,f,est_sent):
            est_sent[r][est_value] = True
            message = _make_message(query_index=query_index,message_type="EST",epoch_number=r,content=est_value)
            broadcast(message)
            logger.debug("Round:{} EST Message reached f+1,value is: {}".format(r,est_value))

        # Output after reaching second threshold
        if _meet_output_condition(est_values,r,est_value,f):
            logger.debug("Round:{} EST Message reached 2f+1,value is:{}".format(r,est_value))
            bin_values[r].add(est_value)
            bv_signal.set()

    def _handle_AUX_message(est_value,sender,r,aux_values,bv_signal):
        if est_value not in (0,1):
            raise InvalidArgsError
        if sender in aux_values[r][est_value]:
            # FIXME: raise or continue? For now will raise just
            # because it appeared first, but maybe the protocol simply
            # needs to continue.
            # raise RedundantMessageError('Redundant AUX received')
            logger.warn("{} Redundant AUX received".format(pid))
            return

        aux_values[r][est_value].add(sender)
        bv_signal.set()
    

    def _recv():
        """main loop"""
        while True:
            sender,msg = receive(query_index)
            if sender not in range(N):continue
            logger.debug("{} receive message:{} from node:{} epoch:{}".format(pid,msg,sender,msg[1]))

            msg_type, r, est_value = msg
            if msg[0] == 'EST':
                _handle_EST_message(r,sender,est_value,est_values,est_sent,bin_values,bv_signal)
            elif msg[0] == 'AUX':
                _handle_AUX_message(est_value,sender,r,aux_values,bv_signal)
            elif msg[0] == 'CONF':
                _handle_CONF_messages(
                    sender=sender,
                    message=msg,
                    conf_values=conf_values,
                    pid=pid,
                    bv_signal=bv_signal,
                )

    input = rpcbase.input_ba
    output = rpcbase.output_ba
    broadcast = rpcbase.broadcast_ba
    receive = rpcbase.receive_ba
    
    # Messages received are routed to either a shared coin, the broadcast, or AUX
    # used in first EST phase
    est_values = defaultdict(lambda: [set(), set()]) 
    est_sent = defaultdict(lambda: [False, False]) # est_send= {round:[bin_val,its values is True or False][sent or not ]}
    aux_values = defaultdict(lambda: [set(), set()]) # used in second AUX phase
    conf_values = defaultdict(lambda: {(0,): set(), (1,): set(), (0, 1): set()}) # used in third CONF phase
    conf_sent = defaultdict(lambda: {(0,): False, (1,): False, (0, 1): False}) # {round:}
    bin_values = defaultdict(set) # bin_values {round:set()} set() value is 0 or 1

    # This event is triggered whenever bin_values or aux_values changes
    bv_signal = Event()
    
    # Run the receive loop in the background
    _thread_recv = gevent.spawn(_recv)

    vi = input(query_index)
    if vi not in (0,1):raise InvalidArgsError
    est = vi 

    r = 0
    already_decided = None

    while True:
        logger.debug('{} start instance:{} aba phase in round:{}'.format(pid,query_index,r))
        
        if _not_broadcast_EST_message(est_sent,r,est): 
            est_sent[r][est] = True
            message = _make_message(query_index=query_index,message_type="EST",epoch_number=r,content=est)
            broadcast(message)

        while len(bin_values[r]) == 0:
            # Block until a value is output
            logger.debug("{} waiting for EST phase value".format(pid))
            bv_signal.clear()
            bv_signal.wait()

        # broadcast AUX message, need receive at least 2f+1 est message
        w = next(iter(bin_values[r]))  # take an element
        message = _make_message(query_index=query_index,message_type="AUX",epoch_number=r,content=w)
        broadcast(message)
        
        values = None

        values = _wati_for_aux_values(bin_values,aux_values,r,N,f,bv_signal)

        # CONF phase
        logger.debug('{} start CONF phase,block until at least N-f({}) CONF values are received'.format(pid,N-f))
        if not conf_sent[r][tuple(values)]:
            values = _wait_for_conf_values(pid,N,f,r,conf_sent,bin_values,values,conf_values,bv_signal,broadcast,j=query_index)

        # Block until receiving the common coin value
        logger.debug('Block until receiving the common coin value')
        
        s = coin(r,query_index)
        
        logger.debug("{} received coin:{} values:{} already_decide:{} in r:{}".format(pid,s,values,already_decided,r))
        est, already_decided = _set_new_estimate(values,s,already_decided,output,query_index)
        logger.debug("{} set_new_est:{} already_decide:{}".format(pid,est,already_decided))

        if already_decided is not None: # already_decided maybe 0
            logger.debug("{} finish ba {} instance,result:{}.".format(pid,query_index,est))
            _thread_recv.kill()
            return
        r += 1

def _set_new_estimate(values, s, already_decided,decide,j):
    if len(values) == 1:
        v = next(iter(values))
        if v == s:
            already_decided = v
            decide(v,j)
        est = v
    else:
        est = s
    return est, already_decided

def _wati_for_aux_values(bin_values,aux_values,r,N,f,bv_signal):
    while True:
    # Block until at least N-f AUX values are received
        if 1 in bin_values[r] and len(aux_values[r][1]) >= N - f:
            return set((1,))

        if 0 in bin_values[r] and len(aux_values[r][0]) >= N - f:
            return set((0,))

        if sum(len(aux_values[r][v]) for v in bin_values[r]) >= N - f:
            return set((0, 1))

        bv_signal.clear()
        bv_signal.wait()


def _handle_CONF_messages(sender, message, conf_values, pid, bv_signal):
    _, r, v = message
    v = tuple(v)
    if v not in ((0,), (1,), (0, 1)):
        raise InvalidArgsError
    if sender in conf_values[r][v]:
        # FIXME: Raise for now to simplify things & be consistent
        # with how other TAGs are handled. Will replace the raise
        # with a continue statement as part of
        # https://github.com/initc3/HoneyBadgerBFT-Python/issues/10
        raise RedundantMessageError('Redundant CONF received')
        
    conf_values[r][v].add(sender)
    bv_signal.set()

def _wait_for_conf_values(pid, N, f, epoch, conf_sent, bin_values,values, conf_values, bv_signal, broadcast,j):
    conf_sent[epoch][tuple(values)] = True
    message = _make_message(query_index=j,message_type="CONF",epoch_number=epoch,content=tuple(bin_values[epoch]))
    broadcast(message)

    while True:
        logger.debug("{} looping CONF phase, conf_values{}".format(pid,conf_values[epoch]))
        
        if 1 in bin_values[epoch] and len(conf_values[epoch][(1,)]) >= N - f:
            return set((1,))
        
        if 0 in bin_values[epoch] and len(conf_values[epoch][(0,)]) >= N - f:
            return set((0,))
        
        if (sum(len(senders) for conf_value, senders in
                conf_values[epoch].items() if senders and
                set(conf_value).issubset(bin_values[epoch])) >= N - f):
            return set((0, 1))

        bv_signal.clear()
        bv_signal.wait()