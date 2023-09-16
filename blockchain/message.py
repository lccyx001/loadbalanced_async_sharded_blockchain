import logging
from datetime import datetime
logger = logging.getLogger(__name__)


valid_messages_type = ["transaction","block"]


class Message(object):

    @staticmethod
    def create(msg_type, content=None):
        if msg_type not in valid_messages_type:
            return False

        new_message =  {'msg_type': msg_type,
                        'content': content,
                        'timestamp': str(datetime.now())}
        return new_message
    
    @staticmethod
    def validate(message):
        # TODO:check valid
        return True

    
    


    