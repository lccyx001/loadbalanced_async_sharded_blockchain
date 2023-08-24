import json
import logging
import datetime

from time import sleep
from .block import Block
from .utils import Utils
from .transaction import Transaction
from .message import Message

class Blockchain(object):
    block = Block()
    utils = Utils()
    def __init__(self, server):
        self.server = server
        self.local_tx = []
        self.count_tx = 0
        self.local_block = None
        self.pow_difficulty = 2

    @property
    def last_block(self):
        if self.server.shared_ledger:
            return self.server.shared_ledger[-1]
        return False

    def get_local_block(self):
        return self.local_block

    def set_local_block(self, block):
        self.local_block = block

    def _get_tx_num(self):
        self.count_tx += 1
        return self.count_tx

    # Block
    def forge_genesis_block(self):
        content = "forge genesis block,content:hello world"
        genesis_block = self.block.forge(0, content, [])
        genesis_block['hash'] = self.utils.compute_hash(genesis_block)
        self.server.shared_ledger.append(genesis_block)
        logging.info('Blockchain: Block: genesis was created.')

    def forge_block(self):
        self.local_block = self.block.forge(self.last_block['index'] + 1,
                                            self.last_block['hash'],
                                            self.server.shared_tx)
        
    def honeybadgerbft(self):
        block = self.local_block
        computed_hash = self.utils.compute_hash(block)
        self.local_block['hash'] = computed_hash

    def validate_previous_hash(self, block_raw):
        last_block = self.last_block
        if not last_block:
            return False
        if block_raw['previous_hash'] != last_block['hash']:
            logging.error('Blockchain: Block: #{} previous_hash is not valid!'.format(block_raw['index']))
            return False
        return True

    def request_add_block(self):
        if not self.local_block:
            logging.info('Blockchain: Block: No one to sent over network!.')
            return False
        if self.server.is_any_node_alive():
            message = Message()
            msg = message.create(msg_type="block",flag=1,content=self.local_block)
            self.server.broadcast(msg)
        self._add_block()

    def receive_block(self,block):
        #TODO:check block valid
        self.local_block = block
        self._add_block()


    def _add_block(self):
        self.server.shared_ledger.append(self.local_block)
        logging.info('Blockchain: Block: #{0} was inserted in the ledger'.format(self.local_block['index']))
        self._clear_shared_tx(self.local_block)
        self._clear_local_block()

    def _clear_local_block(self):
        self.local_block = None

    # Transactions
    def new_tx(self, data):
        tx = Transaction()
        data['index'] = self._get_tx_num()
        tx_raw = tx.new(data)
        if tx_raw:
            self.local_tx.append(tx_raw)
            self._send_tx_to_nodes()
        else:
            self.count_tx -= 1

    def receive_txs(self,txs):
        self.local_tx.extend(txs)
        self._add_tx()
        self._clear_local_tx()

    def _send_tx_to_nodes(self):
        if self.server.is_any_node_alive():
            message = Message()
            msg = message.create(msg_type='transaction',flag=1,content=self.local_tx)
            self.server.broadcast(msg)

        self._add_tx()
        self._clear_local_tx()

    def _add_tx(self):
        for tx in self.local_tx:
            self.server.shared_tx.append(tx)
            logging.info('Blockchain: inserted tx #{0}'.format(tx['index']))

    def _clear_local_tx(self):
        self.local_tx = []

    def _clear_shared_tx(self, block):
        confirmed_txs = [tx['index'] for tx in block['transactions']]
        logging.info('Blockchain: shared txs cleared')
        self.server.shared_tx = [tx for tx in self.server.shared_tx if tx['index'] not in confirmed_txs]