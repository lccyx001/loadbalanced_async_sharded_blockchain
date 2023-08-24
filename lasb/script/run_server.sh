#!/bin/bash
echo "hello world"

for ins in `seq 0 2`
do
    nohup python run_commoncoin.py $ins config.yaml &
done
