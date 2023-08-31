# test scripts

## how to get private key file and public key file?
open `dealer.py` file, edit N,k params to your need.

run ```python dealer.py``` then will produce public key file `pk` and private key file start with `sk`

## how to run commoncoin test?
move files `cc_config.yaml`,`run_server.sh`,`run_commoncoin.py`,`run_cc_test.py` to __honeybadger__ directory.

run `run_server.sh` to start several commoncoin instances.

open a new terminal and run `run_cc_test.py` to test.

## how to run binaryagreement test?
move files `ba_config.yaml`,`run_binaryagreement.py`,`run_ba_test.py` to __honeybadger__ directory.

run ```python run_binaryagreement.py ba_config.yaml``` to start binaryagreement instances.

open a new terminal and run ```python run_ba_test.py``` command to test

## how to run reliablebroadcast test?
move files `rbc_config.yaml`, `run_reliablebroadcast.py`,`run_test_rbc.py` to __honeybadger__ directory.

run ```python run_reliablebroadcast.py rbc_config.yaml``` to start several RBC instances and then the leader index will print on the terminal.

open a new terminal and run ```python run_test_rbc.py {idx}``` replace {idx} with the leader number.


