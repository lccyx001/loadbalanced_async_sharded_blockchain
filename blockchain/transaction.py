class Transaction(object):
    def new(self, data):
        return {'index': data['index'],
                'from_hash': data['from_hash'],
                'to_hash': data['to_hash'],
                'amount': data['amount']}