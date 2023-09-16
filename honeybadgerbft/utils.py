import hashlib
import zfec
import math
import logging
from loadbalanced_async_sharded_blockchain.honeybadgerbft.crypto import threshenc as tpke

logger = logging.getLogger(__name__)
logging.basicConfig(level=logging.INFO,filename="log.log")

def hash(x):
    assert isinstance(x, (str, bytes))
    try:
        x = x.encode()
    except AttributeError:
        pass
    return hashlib.sha256(x).digest()

class ErasureCode(object):
    
    @staticmethod
    def encode(K, N, m):
        """Erasure encodes string ``m`` into ``N`` blocks, such that any ``K``
        can reconstruct.

        :param int K: threshold K
        :param int N: number of blocks to encode string ``m`` into.
        :param bytes m: bytestring to encode.

        :return list: Erasure codes resulting from encoding ``m`` into
            ``N`` blocks using ``zfec`` lib.

        """
        if K > 256: # TODO: Record this assumption!
            return False
        try:
            m = m.encode()
        except AttributeError:
            pass
        encoder = zfec.Encoder(K, N)
        
        # pad m to a multiple of K bytes
        padlen = K - (len(m) % K)
        m += padlen * chr(K-padlen).encode()
        step = len(m)//K
        blocks = [m[i*step: (i+1)*step] for i in range(K)]
        stripes = encoder.encode(blocks)
        return stripes

    @staticmethod
    def decode(K, N, stripes):
        """Decodes an erasure-encoded string from a subset of stripes

        :param list stripes: a container of :math:`N` elements,
            each of which is either a string or ``None``
            at least :math:`K` elements are strings
            all string elements are the same length

        """
        assert len(stripes) == N
        blocks = []
        blocknums = []
        for i, block in enumerate(stripes):
            if block is None:
                continue
            blocks.append(block)
            blocknums.append(i)
            if len(blocks) == K:
                break
        else:
            raise ValueError("Too few to recover")
        decoder = zfec.Decoder(K, N)
        rec = decoder.decode(blocks, blocknums)
        m = b''.join(rec)
        padlen = K - m[-1]
        m = m[:-padlen]
        return m

#####################
#    Merkle tree    #
#####################
def ceil(x): return int(math.ceil(x))

def merkleTree(strList):
    """Builds a merkle tree from a list of :math:`N` strings (:math:`N`
    at least 1)

    :return list: Merkle tree, a list of ``2*ceil(N)`` strings. The root
         digest is at ``tree[1]``, ``tree[0]`` is blank.

    """
    N = len(strList)
    assert N >= 1
    bottomrow = 2 ** ceil(math.log(N, 2))
    mt = [b''] * (2 * bottomrow)
    for i in range(N):
        mt[bottomrow + i] = hash(strList[i])
    for i in range(bottomrow - 1, 0, -1):
        mt[i] = hash(mt[i*2] + mt[i*2+1])
    return mt

def getMerkleBranch(index, mt):
    """Computes a merkle tree from a list of leaves.
    """
    res = []
    t = index + (len(mt) >> 1)
    while t > 1:
        res.append(mt[t ^ 1])  # we are picking up the sibling
        t //= 2
    return res


def merkleVerify(N, val, roothash, branch, index):
    """Verify a merkle tree branch proof
    """
    assert 0 <= index < N
    # XXX Python 3 related issue, for now let's tolerate both bytes and
    # strings
    assert isinstance(val, (str, bytes))
    assert len(branch) == ceil(math.log(N, 2))
    # Index has information on whether we are facing a left sibling or a right sibling
    tmp = hash(val)
    tindex = index
    for br in branch:
        tmp = hash((tindex & 1) and br + tmp or tmp + br)
        tindex >>= 1
    if tmp != roothash:
        logger.error("Verification failed with {} {} {} {}".format(hash(val),roothash,branch,  tmp == roothash))
        return False
    return True

def serialize_UVW(U, V, W):
    # U: element of g1 (65 byte serialized for SS512)
    U = tpke.serialize(U)
    assert len(U) == 65
    # V: 32 byte str
    assert len(V) == 32
    # W: element of g2 (32 byte serialized for SS512)
    W = tpke.serialize(W)
    assert len(W) == 65
    return U, V, W


def deserialize_UVW(U, V, W):
    assert len(U) == 65
    assert len(V) == 32
    assert len(W) == 65
    U = tpke.deserialize1(U)
    W = tpke.deserialize2(W)
    return U, V, W