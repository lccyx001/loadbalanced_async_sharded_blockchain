import json
import logging
logger = logging.getLogger(__name__)

from hashlib import sha256

class Utils(object):
    
    @staticmethod
    def compute_hash(block):
        compute_block = {k:v for k,v in block.items() if k != "timestamp"}
        json_block = Utils.dict_to_json(compute_block)
        return sha256(json_block.encode()).hexdigest()

    @staticmethod
    def json_to_dict(data):
        try:
            dict_data = json.loads(data)
        except Exception as error:
            logger.error('Block: error converting json to dict!')
            logger.error(error)
            return False
        return dict_data

    @staticmethod
    def dict_to_json(data):
        try:
            json_data = json.dumps(data, sort_keys=True)
        except Exception as error:
            logger.error('Block: error converting dict to json!')
            logger.error(error)
            return False
        return json_data
