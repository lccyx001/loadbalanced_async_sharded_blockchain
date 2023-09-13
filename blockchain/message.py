# https://github.com/valvesss/blopy/blob/master/blopy/response.py
import logging

from datetime import datetime
valid_messages_type = ['transaction','block','network']
flag_enum = {1:"new",2:""}

class Message(object):

    def create(self, msg_type, flag, content=[]):
        new_message =  {'msg_type': msg_type,
                        'flag': flag,
                        'content': content,
                        'timestamp': str(datetime.now())}
        
        if self.validate(new_message):
            return new_message
        logging.warning("something wrong when create message",content)
        return None

    @staticmethod
    def validate(message):
        if not (isinstance(message['msg_type'], str) and
                isinstance(message['flag'], int) and
                isinstance(message['content'], (list,dict,)) and
                isinstance(message['timestamp'], str)):
            logging.error('Message: {content} is not valid!',message['content'])
            return False
        
        if message['msg_type'] not in valid_messages_type:
            logging.error('Message: {msg_type} is not valid!')
            return False

        if message['flag'] < 1 or message['flag'] > 100:
            logging.error('Message: {flag} is not valid!')
            return False

        try:
            datetime.strptime(message['timestamp'], '%Y-%m-%d %H:%M:%S.%f')
        except:
            logging.error('Message: {timestamp} is not valid!')
            return False
        return True
    
    


    