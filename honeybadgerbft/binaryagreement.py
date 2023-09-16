import logging
from collections import defaultdict
from loadbalanced_async_sharded_blockchain.honeybadgerbft.exceptions import RedundantMessageError, AbandonedNodeError,InvalidArgsError
import gevent
from gevent.event import Event
from loadbalanced_async_sharded_blockchain.honeybadgerbft.commoncoin import commoncoin
from loadbalanced_async_sharded_blockchain.honeybadgerbft.clientbase import ClientBase

logger = logging.getLogger(__name__)
logging.basicConfig(level=logging.INFO,filename="log.log")


def binaryagreement(sid,pid,N,f,coin:commoncoin,rpcbase:ClientBase,j):
    """
    :param sid: session identifier
    :param pid: my id number
    :param N: the number of parties
    :param f: the number of byzantine parties
    :param coin:CommonCoin.get_coin
    :param rpcbase: RPCBase
    :param j: RPCBase query index

    :return: blocks until
    """
    
    def _recv():
        """main loop"""
        while True:
            sender,msg = receive(j)
            logger.debug("{} receive message:{} from node:{} epoch:{}".format(pid,msg,sender,msg[1]))

            if sender not in range(N):
                logger.error("sender: {} not in N:{}".format(sender,N))
                continue
            
            msg_type, round, est_value = msg
            
            if msg[0] == 'EST':
                if est_value not in (0,1):
                    raise InvalidArgsError
                # BV_Broadcast message
                if sender in est_values[round][est_value]:
                    # FIXME: raise or continue? For now will raise just
                    # because it appeared first, but maybe the protocol simply
                    # needs to continue.
                    
                    logger.warn("{} redundant EST received {}".format(pid,msg))
                    raise RedundantMessageError(
                        'Redundant EST received {}'.format(msg))
                    # return

                est_values[round][est_value].add(sender)
                logger.debug("{} Round:{} receive EST message:{} sender:{}".format(pid,round,est_value,sender))
                # Relay after reaching first threshold
                # more than f + 1 BA nodes have received round round's EST message，means this message is free fault crash, just broadcast it.
                logger.debug("{} Round:{}  sender:{} threhold:{}".format(pid,round,sender,len(est_values[round][est_value])))
                if len(est_values[round][est_value]) >= f + 1 and not est_sent[round][est_value]:
                    est_sent[round][est_value] = True
                    broadcast((j,('EST', round, est_value)))
                    logger.debug("Round:{} EST Message reached f+1,value is: {}".format(round,est_value))

                # Output after reaching second threshold
                # more than f + 1 BA nodes have received round round's EST message，means this message is free byzantine crash, just broadcast it.
                if len(est_values[round][est_value]) >= 2 * f + 1:
                    logger.debug("Round:{} EST Message reached 2f+1,value is:{}".format(round,est_value))
                    bin_values[round].add(est_value)
                    bv_signal.set()

            elif msg[0] == 'AUX':
                # AUX message
                if est_value not in (0,1):
                    raise InvalidArgsError
                if sender in aux_values[round][est_value]:
                    # FIXME: raise or continue? For now will raise just
                    # because it appeared first, but maybe the protocol simply
                    # needs to continue.
                    raise RedundantMessageError(
                        'Redundant AUX received {}'.format(msg))
                    # logger.warn("{} Redundant AUX received {}".format(pid,msg))
                    # return

                aux_values[round][est_value].add(sender)
                bv_signal.set()
                
            elif msg[0] == 'CONF':
                _handle_conf_messages(
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

    vi = input(j)
    if vi not in (0,1):raise InvalidArgsError
    est = vi 
    r = 0
    already_decided = None
    while True:
        logger.debug('{} Starting with est = {} in epoch {}'.format(pid,est,r))
        
        if not est_sent[r][est]:
            est_sent[r][est] = True
            broadcast((j , ("EST",r,est)) )

        while len(bin_values[r]) == 0:
            # Block until a value is output
            logger.debug("{} waiting for EST phase value".format(pid))
            bv_signal.clear()
            bv_signal.wait()

        # broadcast AUX message, need receive at least 2f+1 est message
        w = next(iter(bin_values[r]))  # take an element
        broadcast((j, ('AUX', r, w)))
        values = None

        while True:
            logger.debug("{}:AUX phase round:{} bin_values:{} aux_values:{}".format(pid,r,
                                                                                    bin_values[r],
                                                                                    aux_values[r]))
            # Block until at least N-f AUX values are received
            if 1 in bin_values[r] and len(aux_values[r][1]) >= N - f:
                values = set((1,))
                
                break
            if 0 in bin_values[r] and len(aux_values[r][0]) >= N - f:
                values = set((0,))
                
                break
            if sum(len(aux_values[r][v]) for v in bin_values[r]) >= N - f:
                values = set((0, 1))
                
                break
            bv_signal.clear()
            bv_signal.wait()

        # CONF phase
        logger.debug('{} start CONF phase,block until at least N-f({}) CONF values are received'.format(pid,N-f))
        if not conf_sent[r][tuple(values)]:
            values = _wait_for_conf_values(pid=pid,
                N=N,
                f=f,
                epoch=r,
                conf_sent=conf_sent,
                bin_values=bin_values,
                values=values,
                conf_values=conf_values,
                bv_signal=bv_signal,
                broadcast=broadcast,j=j)

        # Block until receiving the common coin value
        logger.debug('Block until receiving the common coin value')
        s = coin(r,j)

        try:
            est, already_decided = _set_new_estimate(values,s,already_decided,output,j)
            logger.debug("{} finish ba phase!".format(pid))
        except AbandonedNodeError:
            logger.warn("{}:{} Quit! AbandonedNodeError".format(pid,j))
            _thread_recv.kill()
            return
        r += 1

def _set_new_estimate(values, s, already_decided,decide,j):
    if len(values) == 1:
        v = next(iter(values))
        if v == s:
            if already_decided is None:
                already_decided = v
                decide(v,j)
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
    return est, already_decided

def _handle_conf_messages(sender, message, conf_values, pid, bv_signal):
    _, r, v = message
    v = tuple(v)
    if v not in ((0,), (1,), (0, 1)):
        raise InvalidArgsError
    if sender in conf_values[r][v]:
        # FIXME: Raise for now to simplify things & be consistent
        # with how other TAGs are handled. Will replace the raise
        # with a continue statement as part of
        # https://github.com/initc3/HoneyBadgerBFT-Python/issues/10
        raise RedundantMessageError(
            'Redundant CONF received {}'.format(message))
        # logger.warn("{} Redundant CONF received {}".format(pid,message))
        # return

    conf_values[r][v].add(sender)
    bv_signal.set()

def _wait_for_conf_values(pid, N, f, epoch, conf_sent, bin_values,values, conf_values, bv_signal, broadcast,j):
    conf_sent[epoch][tuple(values)] = True
    broadcast((j, ('CONF', epoch, tuple(bin_values[epoch]))))

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