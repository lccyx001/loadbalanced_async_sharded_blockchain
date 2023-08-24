from .utils import Utils

class Transaction(object):
    def new(self, data):
        if self.validate(data):
            return {'index': data['index'],
                    'from_hash': data['from_hash'],
                    'to_hash': data['to_hash'],
                    'amount': data['amount']}
        return False

    def validate(self, data):
        tx_required_items = {   'index': int,
                                'from_hash': str,
                                'to_hash': str,
                                'amount': int}
        utils = Utils()
        if utils.validate_dict_keys(data, tx_required_items) and \
            utils.validate_dict_values(data, tx_required_items):
            return True
        return False