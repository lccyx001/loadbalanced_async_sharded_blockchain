from datetime import datetime

class Block(object):

    @staticmethod
    def forge(index,previous_hash,transactions,shard=None):
        block = {'index': index,
                 'nonce': 0,
                 'previous_hash': previous_hash,
                 'timestamp': str(datetime.now()),
                 'transactions': transactions}
        if shard:
            block['shard'] = shard
        return block

