import gevent
import logging
from rpcbase import RPCBase

logger = logging.getLogger(__name__)
logging.basicConfig(level=logging.INFO,filename="log.log")

def commonsubset(pid, N, f, rbc_out:RPCBase.rbc_out, aba_in:RPCBase.aba_in, aba_out:RPCBase.aba_out):
    """The BKR93 algorithm for asynchronous common subset.

    :param pid: my identifier
    :param N: number of nodes
    :param f: fault tolerance
    :param rbc_out: an array of :math:`N` (blocking) output functions,
        returning a string
    :param aba_in: an array of :math:`N` (non-blocking) functions that
        accept an input bit
    :param aba_out: an array of :math:`N` (blocking) output functions,
        returning a bit
    :return: an :math:`N`-element array, each element either ``None`` or a
        string
    """
    def _recv_rbc(j):
        # Receive output from reliable broadcast
        rbc_values[j] = rbc_out(j)
        logger.info("{} index:{} receive rbc out:{}".format(pid,j,rbc_values[j]))
        if not aba_inputted[j]:
            # Provide 1 as input to the corresponding bin agreement
            aba_inputted[j] = True
            logger.info("{} aba_in:{}".format(pid,j))
            aba_in(1,j)

    def _recv_aba(j):
        # Receive output from binary agreement
        aba_values[j] = aba_out(j)  # May block
        logger.info("{}: index:{} aba_out value:{}".format(pid,j,aba_values[j]))

        if sum(aba_values) >= N - f:
            # Provide 0 to all other aba
            for k in range(N):
                if not aba_inputted[k]:
                    aba_inputted[k] = True
                    logger.info("{}: index:{} provide 0 to {} aba".format(pid,j,k))
                    aba_in(0,k)

    aba_inputted = [False] * N
    aba_values = [0] * N
    rbc_values = [None] * N

    r_threads = [gevent.spawn(_recv_rbc, j) for j in range(N)]
    # Wait for all binary agreements
    a_threads = [gevent.spawn(_recv_aba, j) for j in range(N)]
    logger.info("{} acs init threads ".format(pid))

    gevent.joinall(a_threads)
    logger.info("{} finish recv aba threads aba_values:{}".format(pid,aba_values))
    assert sum(aba_values) >= N - f  # Must have at least N-f committed

    # Wait for the corresponding broadcasts
    for j in range(N):
        if aba_values[j]:
            r_threads[j].join()
            assert rbc_values[j] is not None
        else:
            r_threads[j].kill()
            rbc_values[j] = None

    return tuple(rbc_values)
