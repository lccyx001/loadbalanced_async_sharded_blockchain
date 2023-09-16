class Transaction(object):
    
    @staticmethod
    def new(data):
        return {'index': data['index'],
                'from_hash': data['from_hash'],
                'to_hash': data['to_hash'],
                'amount': data['amount']}
    
    @staticmethod
    def validate(transaction:dict):
        valid_keys = ["index","from_hash","to_hash","amout"]
        if len(transaction.keys()) != 4:
            return False
        
        for key in transaction.keys():
            if key not in valid_keys:
                return False
        return True