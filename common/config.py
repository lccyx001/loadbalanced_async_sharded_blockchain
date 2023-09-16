import yaml
from loadbalanced_async_sharded_blockchain.honeybadgerbft.crypto.threshsig.boldyreva import TBLSPrivateKey,TBLSPublicKey
from loadbalanced_async_sharded_blockchain.honeybadgerbft.crypto.threshenc import TPKEPrivateKey,TPKEPublicKey

class CommonConfig(object):

    def __init__(self,file_name= "config.yaml") -> None:
        self._config = self._load_common(file_name)
        self._pk = None
        self._epk = None
        self._N = None
        self._f = None

    def _load_common(self,filename):
        with open(filename,'r') as yf:
            stream = yf.read()
        config = yaml.load(stream,yaml.SafeLoader)
        common_config = config.get("common")
        return common_config
    
    @property
    def config(self,):
        return self._config
    
    @property
    def PK(self):
        if not self._pk:
            with open(self.config.get("pk"),"rb") as f:
                pk = f.read()
            pk = TBLSPublicKey.deserialize(pk)
            public_key = TBLSPublicKey.from_dict(pk)
            self._pk = public_key
        return self._pk
    
    @property
    def ePK(self):
        if not self._epk:
            with open(self.config.get("epk"),"rb") as f:
                epk = f.read()
            epk = TPKEPublicKey.deserialize(epk)
            epublic_key = TPKEPublicKey.from_dict(epk)
            self._epk = epublic_key
        return self._epk


class InstanceConfig(object):

    def __init__(self,id) -> None:
        self._sk = None
        self._id = id
        self._config = self._load_instance()
        self._esk = None
        
    def _load_instance(self):
        with open("config.yaml",'r') as yf:
            stream = yf.read()
        config = yaml.load(stream,yaml.SafeLoader)
        return config.get("honeybadger{}".format(self._id))
    
    @property
    def SK(self):
        if not self._sk:
            with open("sk{}".format(self._id),"rb") as f:
                sk = f.read()
            sk = TBLSPrivateKey.deserialize(sk)
            private_key = TBLSPrivateKey.from_dict(sk)
            self._pk = private_key
        return self._pk
    
    @property
    def eSK(self):
        if not self._esk:
            with open("esk{}".format(self._id),"rb") as f:
                esk = f.read()
            esk = TPKEPrivateKey.deserialize(esk)
            eprivate_key = TPKEPrivateKey.from_dict(esk)
            self._esk = eprivate_key
        return self._esk

    @property
    def config(self,):
        return self._config

class BlockchainConfig(object):

    def __init__(self) -> None:
        pass

class Config(object):

    def __init__(self, id, ) -> None:
        self._id = id
        self._cc_config = CommonConfig()
        self._instance_config = InstanceConfig(id)


    @property
    def id(self):
        return self._id

    @property
    def PK(self):
        return self._cc_config.PK
    
    @property
    def ePK(self):
        return self._cc_config.ePK
    
    @property
    def eSK(self):
        return self._instance_config.eSK
    
    @property
    def SK(self):
        return self._instance_config.SK
    
    @property
    def N(self):
        return self._cc_config.config.get("N")
    
    @property
    def f(self):
        return self._cc_config.config.get("f")
    
    @property
    def host(self):
        return self._instance_config.config["host"]
    
    @property
    def port(self):
        return self._instance_config.config["port"]
    
    @property
    def channels(self):
        return self._instance_config.config["channels"]

