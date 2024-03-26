# 负载均衡异步分片区块链

一个负载均衡的异步区块链demo

## 环境构建

安装docker charm基础环境
```sh
docker pull lccyx001/dagbc
```

启动镜像以dagbc-charm命名
```sh
docker run --name dagbc-charm  -p 2000:2000 -p 2010:2010 -p 2020:2020 -p 2030:2030 -p 2040:2040 -p 2050:2050 -p 2060:2060 -p 2070:2070 -p 2001:2001 -p 2011:2011 -p 2021:2021 -p 2031:2031 -p 2041:2041 -p 2051:2051 -p 2061:2061 -p 2071:2071 -itd lccyx001/dagbc
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

## 测试1

在不同机器上执行下面的步骤
```sh
cd blockchain/test/
```

修改test_node.yaml 文件中的分片参数，N参数，先运行dealer.py,生成分片1的所有配置以及公私钥文件
```sh
python dealer.py shard1 a
```

启动node1节点，生成测试数据，等待其他节点进行共识
```sh
python test_node.py 1
```

切换其他节点，更新公私钥文件（通过git pull），生成分片2的配置
```sh
python dealer.py shard2
```
启动分片2的节点
```sh
python test_node.py 2
```

按下任意键进行共识。
