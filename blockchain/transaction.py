
class Transaction(object):
    
    @staticmethod
    def new(data):
        return {'index': data['index'],
                'from_hash': data['from_hash'],
                'to_hash': data['to_hash'],
                'amount': data['amount']}
    
    @staticmethod
    def validate(transaction:dict,account_db):
        valid_keys = ["index","from_hash","to_hash","amount"]
        if len(transaction.keys()) != 4:
            return False
        
        for key in transaction.keys():
            if key not in valid_keys:
                return False
        
        if transaction["amount"] < 0:
            return False
        
        from_hash = transaction["from_hash"]
        amount = transaction['amount']
        if not account_db.check_balance(from_hash,amount):
            return False
        return True