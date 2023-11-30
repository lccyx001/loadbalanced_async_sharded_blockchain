from collections import defaultdict
import logging
logger = logging.getLogger(__name__)
logging.basicConfig(level=logging.INFO,filename="log.log")

class Account(object):

    def __init__(self) -> None:
        self._accounts_db = defaultdict()
    
    def get(self,account_hash):
        return self._accounts_db.get(account_hash)
    
    def _update(self,account_hash,value):
        assert isinstance(value,int) 
        if not self.get(account_hash):
            self._accounts_db[account_hash] = value
        else:
            self._accounts_db[account_hash] += value
    
    def add_value(self,account_hash,value):
        assert value > 0
        self._update(account_hash,value)

    def decrease_value(self, account_hash,value):
        assert value > 0
        self._update(account_hash,-value)

    def check_balance(self,account_hash,value):
        if not self.get(account_hash): return False
        return self.get(account_hash) > value

    def execute_transaction(self,tx):
        from_hash, to_hash, amount = tx["from_hash"], tx["to_hash"], tx["amount"]
        if not self.check_balance(from_hash,amount):
            logger.error("invalid tx:{}".format(tx))
            return False
        self.decrease_value(from_hash,amount)
        self.add_value(to_hash,amount)

    def mock_account(self,account_hash):
        self.add_value(account_hash,1000000000)
