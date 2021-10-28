#!/bin/bash

git clone git@gitlab.tocraw.com:root/trade_bot_protobuf.git

protoc -I=. --python_out=. --mypy_out=. ./trade_bot_protobuf/src/*.proto

mv ./trade_bot_protobuf/src/*_pb2.py ./src/protobuf
mv ./trade_bot_protobuf/src/*_pb2.pyi ./src/protobuf

rm -rf trade_bot_protobuf