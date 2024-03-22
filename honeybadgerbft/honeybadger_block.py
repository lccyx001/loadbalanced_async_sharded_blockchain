from loadbalanced_async_sharded_blockchain.honeybadgerbft.crypto import threshenc as tpke
from loadbalanced_async_sharded_blockchain.honeybadgerbft.utils import serialize_UVW,deserialize_UVW
from loadbalanced_async_sharded_blockchain.honeybadgerbft.crypto.threshenc import TPKEPrivateKey,TPKEPublicKey
import os
import pickle
import logging

logger = logging.getLogger(__name__)
logging.basicConfig(level=logging.INFO,filename="log.log")

def honeybadger_block(pid, N, f, ePK:TPKEPublicKey, eSK:TPKEPrivateKey, acs_out,rpcbase):
    """The HoneyBadgerBFT algorithm for a single block

    :param pid: my identifier
    :param N: number of nodes
    :param f: fault tolerance
    :param ePK: threshold encryption public key
    :param eSK: threshold encryption secret key
    :param acs_out: a blocking function that returns an array of ciphertexts acs.get() 
    :return:
    """
    def encrypt(proposed):
        # Threshold encrypt
        # TODO: check that propose_in is the correct length, not too large
        key = os.urandom(32)    # random 256-bit key
        ciphertext = tpke.encrypt(key, proposed)
        tkey = ePK.encrypt(key)

        to_acs = pickle.dumps((serialize_UVW(*tkey), ciphertext))
        return to_acs

    def broadcast_shares(vall):
        my_shares = []
        for i, v in enumerate(vall):
            if v is None:
                my_shares.append(None)
                continue
            (tkey, ciph) = pickle.loads(v)
            tkey = deserialize_UVW(*tkey)
            share = eSK.decrypt_share(*tkey)
            # share is of the form: U_i, an serialized element of group1
            my_shares.append(tpke.group.serialize(share,compression=True))
        tpke_bcast(my_shares)


    def receive_all_shares(shares_received):
        while len(shares_received) < f+1:
            (j, shares) = tpke_recv()
            if j in shares_received:
                # TODO: alert that we received a duplicate
                logger.warn('Received a duplicate decryption share from {}'.format(j))
                continue
            shares_received[j] = shares
        assert len(shares_received) >= f+1


    def decrypt(vall,shares_received):
        # TODO: Accountability
        # If decryption fails at this point, we will have evidence of misbehavior,
        # but then we should wait for more decryption shares and try again
        decryptions = []
        for i, v in enumerate(vall):
            if v is None:
                continue
            svec = {}
            for j, shares in shares_received.items():
                svec[j] = tpke.group.deserialize(shares[i],compression=True)      # Party j's share of broadcast i
            (tkey, ciph) = pickle.loads(v)
            tkey = deserialize_UVW(*tkey)
            key = ePK.combine_shares(*tkey, svec)
            plain = tpke.decrypt(key, ciph)
            if(not isinstance(plain,bytes)):
                logger.error("plain not bytes:{}".format(plain))
                continue
            decryptions.append(plain.decode())
        return decryptions
        

    acs_in = rpcbase.acs_in # a function to provide input to acs routine
    propose_in = rpcbase.propose_in # a function returning a sequence of transactions
    tpke_bcast = rpcbase.tpke_bcast
    tpke_recv = rpcbase.tpke_receive
    # Broadcast inputs are of the form (tenc(key), enc(key, transactions))

    prop = propose_in()
    to_acs = encrypt(prop)
    acs_in(to_acs)
    # logger.info("{} input encrypt proposed value to acs.".format(pid))
    
    # Wait for the corresponding ACS to finish
    vall = acs_out()
    assert len(vall) == N
    assert len([_ for _ in vall if _ is not None]) >= N - f  # This many must succeed
    # logger.info("{} Received from acs".format(pid))

    # Broadcast all our decryption shares
    broadcast_shares(vall)
    # logger.info("{} broadcast shares".format(pid))

    # Receive everyone's shares
    shares_received = {}
    receive_all_shares(shares_received)
    
    # assert len(shares_received) == N
    # logger.info("{} Receive shares".format(pid))
    decryptions = decrypt(vall,shares_received)
    # logger.info("{} honeybadgerBFT Done!".format(pid))
    
    return tuple(decryptions)
