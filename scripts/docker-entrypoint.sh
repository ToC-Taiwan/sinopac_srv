#!/bin/bash

# mosquitto -c /sinopac_srv/configs/mosquitto/mosquitto.conf -d
python /sinopac_srv/src/main.py ${PYPORT} ${GOLANGPORT} ${TRADEID} ${TRADEPASS} ${CAPASS}
