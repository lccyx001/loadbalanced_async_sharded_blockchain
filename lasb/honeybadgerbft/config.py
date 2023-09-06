import yaml
from crypto.threshsig.boldyreva import TBLSPublicKey,TBLSPrivateKey


class CommonConfig(object):

    def __init__(self,file_name= "config.yaml") -> None:
        self._config = self._load_common(file_name)
        self._pk = None
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

    
class InstanceConfig(object):

    def __init__(self,id) -> None:
        self._sk = None
        self._id = id
        self._config = self._load_instance()
        

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
    def config(self,):
        return self._config


class Config(object):

    def __init__(self, id, ) -> None:
        self._id = id
        self.cc_config = CommonConfig()
        self.instance_config = InstanceConfig(id)

        self._cc_channels = None
        self._ba_channels = None
        self._rbc_channels = None        

        self._cc_ports = None
        self._ba_ports = None
        self._rbc_ports = None

    @property
    def id(self):
        return self._id

    @property
    def PK(self):
        return self.cc_config.PK
    
    @property
    def SK(self):
        return self.instance_config.SK
    
    @property
    def N(self):
        return self.cc_config.config.get("N")
    
    @property
    def f(self):
        return self.cc_config.config.get("f")
    
    @property
    def host(self):
        return self.instance_config.config["host"]
    
    @property
    def port(self):
        return self.instance_config.config["port"]
    
    @property
    def channels(self):
        return self.instance_config.config["channels"]

    # @property
    # def cc_host(self):
    #     return self.instance_config.config["cc"]["host"]

    # @property
    # def cc_start_port(self):
    #     return self.instance_config.config["cc"]["port"]

    # @property
    # def cc_ports(self):
    #     if not self._cc_ports:
    #         ports = []
    #         start_port = self.cc_start_port + self._id * 10 
    #         for i in range(self.N):
    #             port = start_port + i
    #             ports.append(port)
    #         self._cc_ports = ports
    #     return self._cc_ports

    # @property
    # def cc_channels(self):
    #     if not self._cc_channels:
    #         cc_channels = {} #{2000:[(1,tcp://127.0.0.1:2011),(2,tcp://127.0.0.1:2021)]}
    #         ports = self.cc_ports
    #         for idx ,local_port in enumerate(ports): # 2000
    #             channels = []
    #             address = "tcp://{}:{}"
    #             for i in range(self.N):
    #                 if i == self._id:
    #                     continue
    #                 _port = self.cc_start_port + i * 10 + idx
    #                 channel = (i,address.format(self.cc_host,_port))
    #                 channels.append(channel)
    #             cc_channels[local_port] = channels
    #         self._cc_channels = cc_channels
    #     return self._cc_channels
    
    # @property
    # def ba_start_port(self):
    #     return self.instance_config.config["ba"]["port"]

    # @property
    # def ba_ports(self):
    #     if not self._ba_ports:
    #         ports = []
    #         start_port = self.ba_start_port + self._id * 10
    #         for i in range(self.N):
    #             port = start_port + i
    #             ports.append(port)
    #         self._ba_ports = ports
    #     return self._ba_ports
        

    # @property
    # def ba_host(self):
    #     return self.instance_config.config["ba"]["host"]

    # @property
    # def ba_channels(self):
    #     if not self._ba_channels:
    #         ba_channels = {} #{2000:[(1,tcp://127.0.0.1:2011),(2,tcp://127.0.0.1:2021)]}
    #         ports = self.ba_ports
    #         for idx ,local_port in enumerate(ports): # 2000
    #             channels = []
    #             address = "tcp://{}:{}"
    #             for i in range(self.N):
    #                 if i == self._id:
    #                     continue
    #                 _port = self.ba_start_port + i * 10 + idx
    #                 channel = (i,address.format(self.ba_host,_port))
    #                 channels.append(channel)
    #             ba_channels[local_port] = channels
    #         self._ba_channels = ba_channels
    #     return self._ba_channels
    
    # @property
    # def rbc_host(self):
    #     return self.instance_config.config["rbc"]["host"]
    
    # @property
    # def rbc_start_port(self):
    #     return self.instance_config.config["rbc"]["port"]

    # @property
    # def rbc_ports(self):
    #     if not self._rbc_ports:
    #         ports = []
    #         start_port = self.rbc_start_port + self._id * 10
    #         for i in range(self.N):
    #             port = start_port + i
    #             ports.append(port)
    #         self._rbc_ports = ports
    #     return self._rbc_ports

    # @property
    # def rbc_channels(self):
    #     if not self._rbc_channels:
    #         rbc_channels = {} #{2000:[(1,tcp://127.0.0.1:2011),(2,tcp://127.0.0.1:2021)]}
    #         ports = self.rbc_ports
    #         for idx ,local_port in enumerate(ports): # 2000
    #             channels = []
    #             address = "tcp://{}:{}"
    #             for i in range(self.N):
    #                 if i == self._id:
    #                     continue
    #                 _port = self.rbc_start_port + i * 10 + idx
    #                 channel = (i,address.format(self.ba_host,_port))
    #                 channels.append(channel)
    #             rbc_channels[local_port] = channels
    #         self._rbc_channels = rbc_channels
    #     return self._rbc_channels
