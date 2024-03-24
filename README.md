# 负载均衡异步分片区块链

一个负载均衡的异步区块链demo

## 环境构建

安装docker charm基础环境
```sh
docker pull lccyx001/dagbc
```

启动镜像以dagbc-charm命名
```sh
docker run --name dagbc-charm -itd lccyx001/dagbc 
```

安装vscode,下载下面的插件
"Docker"
"DEV Containers"
"Remote - ssh"

安装Python环境
```sh
cd /root/loadbalanced_async_sharded_blockchain
pip install -r requirement
```

## 启动服务
启动区块链服务
```
```


运行共识模块
```
```

A loadbalanced async sharded blockchain demo.

Now under developing.

How to eastablish it?

Install docker

```
docker pull sbellem/charm-crypto
```

Update dependencys:
```
sudo apt install gcc 
sudo apt-get install -y autoconf automake build-essential libffi-dev libtool pkg-config python3-dev
apt-get install libgmp3-dev
```

TODO list:

```
1. Using DAG 
2. Blockchain ledger out of memory
3. Using loadbalancing
4. Blockchain concensus can run multiple rounds
```
