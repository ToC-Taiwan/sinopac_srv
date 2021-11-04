#!/bin/bash

url=https://mopsfin.twse.com.tw/opendata/t187ap03_L.csv
HTTP_CODE=$(curl -fSL $url --output ./data/stock_tse.csv --write-out "%{http_code}" "$@")
if [[ ${HTTP_CODE} -lt 200 || ${HTTP_CODE} -gt 299 ]] ; then
    exit 1
fi

url=http://mopsfin.twse.com.tw/opendata/t187ap03_O.csv
HTTP_CODE=$(curl -fSL $url --output ./data/stock_otc.csv --write-out "%{http_code}" "$@")
if [[ ${HTTP_CODE} -lt 200 || ${HTTP_CODE} -gt 299 ]] ; then
    rm ./data/tmp_tse.csv
    exit 1
fi

# /bin/rm ./data/stock_tse.csv
# /bin/rm ./data/stock_otc.csv
# /bin/mv ./data/tmp_tse.csv ./data/stock_tse.csv
# /bin/mv ./data/tmp_otc.csv ./data/stock_otc.csv

