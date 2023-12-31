"""An implementation of (unique) threshold signatures based on
Gap-Diffie-Hellman Boldyreva, 2002 https://eprint.iacr.org/2002/118.pdf

Dependencies:
    Charm, http://jhuisi.github.io/charm/ a wrapper for PBC (Pairing
    based crypto)

"""
from charm.toolbox.pairinggroup import PairingGroup, ZR, G1, G2, pair
from base64 import encodestring, decodestring
from operator import mul
from functools import reduce
import pickle
# group = PairingGroup('SS512')
# group = PairingGroup('MNT159')
group = PairingGroup('MNT224')


def serialize(g):
    """ """
    # Only work in G1 here
    return decodestring(group.serialize(g)[2:])


def deserialize0(g):
    """ """
    # Only work in G1 here
    return group.deserialize(b'0:'+encodestring(g))


def deserialize1(g):
    """ """
    # Only work in G1 here
    return group.deserialize(b'1:'+encodestring(g))


def deserialize2(g):
    """ """
    # Only work in G1 here
    return group.deserialize(b'2:'+encodestring(g))


g1 = group.hash('geng1', G1)
g1.initPP()
# g2 = g1
g2 = group.hash('geng2', G2)
g2.initPP()
ZERO = group.random(ZR, seed=59)*0
ONE = group.random(ZR, seed=60)*0+1


def polynom_eval(x, coefficients):
    """Polynomial evaluation."""
    y = ZERO
    xx = ONE
    for coeff in coefficients:
        y += coeff * xx
        xx *= x
    return y


class TBLSPublicKey(object):
    """ """
    def __init__(self, l, k, VK, VKs):
        """ """
        self.l = l  # noqa: E741
        self.k = k
        self.VK = VK
        self.VKs = VKs

    # def __getstate__(self):
    #     """ """
    #     d = dict(self.__dict__)
    #     d['VK'] = serialize(self.VK)
    #     d['VKs'] = list(map(serialize, self.VKs))
    #     return d

    # def __setstate__(self, d):
    #     """ """
    #     self.__dict__ = d
    #     self.VK = deserialize2(self.VK)
    #     self.VKs = list(map(deserialize2, self.VKs))
    #     print("I'm being depickled")

    def lagrange(self, S, j):
        """ """
        # Assert S is a subset of range(0,self.l)
        assert len(S) == self.k
        assert type(S) is set
        assert S.issubset(range(0, self.l))
        S = sorted(S)

        assert j in S
        assert 0 <= j < self.l
        num = reduce(mul, [0 - jj - 1 for jj in S if jj != j], ONE)
        den = reduce(mul, [j - jj     for jj in S if jj != j], ONE)  # noqa: E272
        # assert num % den == 0
        return num / den

    def hash_message(self, m):
        """ """
        return group.hash(m, G1)

    def verify_share(self, sig, i, h):
        """ """
        assert 0 <= i < self.l
        B = self.VKs[i]
        assert pair(sig, g2) == pair(h, B)
        return True

    def verify_signature(self, sig, h):
        """ """
        assert pair(sig, g2) == pair(h, self.VK)
        return True

    def combine_shares(self, sigs):
        """ """
        # sigs: a mapping from idx -> sig
        # sig
        S = set(sigs.keys())
        assert S.issubset(range(self.l))

        res = reduce(mul,
                     [sig ** self.lagrange(S, j)
                      for j, sig in sigs.items()], 1)
        return res
    
    def serialize(self,):
        data = {'l':self.l,'k':self.k,"VK":group.serialize(self.VK,compression=True),"VKs":list(map(lambda x:group.serialize(x,compression=True), self.VKs))}
        data = pickle.dumps(data)
        return  data

    @staticmethod        
    def deserialize(data):
        obj_dict = pickle.loads(data)
        obj_dict['VK'] = group.deserialize(obj_dict['VK'],compression=True)
        obj_dict['VKs'] = list(map(lambda x:group.deserialize(x,compression=True), obj_dict['VKs']))
        return obj_dict
    
    @classmethod
    def from_dict(cls,data_dict):
        return cls(data_dict['l'],data_dict['k'],data_dict['VK'],data_dict['VKs'])

class TBLSPrivateKey(TBLSPublicKey):
    """ """

    def __init__(self, l, k, VK, VKs, SK, i):
        """ """
        super(TBLSPrivateKey, self).__init__(l, k, VK, VKs)
        assert 0 <= i < self.l
        self.i = i
        self.SK = SK

    def sign(self, h):
        """ """
        return h ** self.SK

    def serialize(self,):
        data = {'l':self.l,'k':self.k,'i':self.i,
                "VK":group.serialize(self.VK,compression=True),
                "VKs":list(map(lambda x:group.serialize(x,compression=True), self.VKs)),
                "SK":group.serialize(self.SK,compression=True)}
        data = pickle.dumps(data)
        return  data

    @staticmethod        
    def deserialize(data):
        obj_dict = pickle.loads(data)
        obj_dict['VK'] = group.deserialize(obj_dict['VK'],compression=True)
        obj_dict['VKs'] = list(map(lambda x:group.deserialize(x,compression=True), obj_dict['VKs']))
        obj_dict['SK'] = group.deserialize(obj_dict['SK'],compression=True)
        return obj_dict
    
    @classmethod
    def from_dict(cls,data_dict):
        return cls(data_dict['l'],data_dict['k'],data_dict['VK'],data_dict['VKs'],data_dict['SK'],data_dict['i'])

def dealer(players=10, k=5, seed=None):
    """ """
    # Random polynomial coefficients
    a = group.random(ZR, count=k, seed=seed)
    assert len(a) == k
    secret = a[0]

    # Shares of master secret key
    SKs = [polynom_eval(i, a) for i in range(1, players+1)]
    assert polynom_eval(0, a) == secret

    # Verification keys
    VK = g2 ** secret
    VKs = [g2 ** xx for xx in SKs]

    public_key = TBLSPublicKey(players, k, VK, VKs)
    private_keys = [TBLSPrivateKey(players, k, VK, VKs, SK, i)
                    for i, SK in enumerate(SKs)]

    # Check reconstruction of 0
    S = set(range(0, k))
    lhs = polynom_eval(0, a)
    rhs = sum(public_key.lagrange(S, j) * polynom_eval(j+1, a) for j in S)
    assert lhs == rhs
    # print i, 'ok'

    return public_key, private_keys
