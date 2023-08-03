
class Blocks:
    pass

class Transaction:
    """交易"""
    _from_hash = ""
    _to_hash = ""
    _amount = 0
    _self_hash = ""

    def __init__(self,from_hash,to_hash,amount) -> None:
        self._from_hash = from_hash
        self._to_hash = to_hash
        self._amount = amount
        self._self_hash = self._hash()
    
    def _hash(self,):
        return ""

class P2PServer:
    pass

class User:
    pass


