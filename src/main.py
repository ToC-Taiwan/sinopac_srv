#!/usr/local/bin/python
# -*- coding: utf-8 -*-
'''SINOPAC PYTHON API FORWARDER'''
from re import search
from datetime import datetime
import threading
import time
import logging
import sys
import csv
import os
import typing
import subprocess
import requests
import shioaji as sj
from flask import Flask,  request, jsonify, make_response
from flasgger import Swagger
from waitress import serve
from shioaji import BidAskSTKv1, TickSTKv1, Exchange, constant, error, TickFOPv1
from protobuf import tradeevent_pb2, bidask_pb2, streamtick_pb2, \
    traderecord_pb2, snapshot_pb2, volumerank_pb2, entiretick_pb2, kbar_pb2

log_format = '%(asctime)s - %(name)s - %(levelname)s - %(message)s'
logging.basicConfig(level=logging.INFO, format=log_format, stream=sys.stdout)
session = requests.Session()
api = Flask(__name__)
swagger = Swagger(api)
token = sj.Shioaji()
trade_bot_port = sys.argv[2]
mutex = threading.Lock()
deployment = os.getenv('DEPLOYMENT')

TRADE_BOT_HOST = str()
if deployment == 'docker':
    TRADE_BOT_HOST = 'toc-trader.tocraw.com'

SERVER_STATUS = int()
UP_TIME = int()
RE_LOGGING = False
TRADE_ID = sys.argv[3]
TRADE_PASSWD = sys.argv[4]
CA_PASSWD = sys.argv[5]

ALL_STOCK_NUM_LIST: typing.List[str] = []
BIDASK_SUB_LIST: typing.List[str] = []
QUOTE_SUB_LIST: typing.List[str] = []
FUTURE_SUB_LIST: typing.List[str] = []
ERROR_TIMES = int()


@ api.route('/pyapi/basic/importstock', methods=['GET'])
def import_stock():
    ''' Get All stock from csv
    ---
    tags:
      - basic
    responses:
      200:
        description: Success Response
      500:
        description: Server Not Ready
    '''
    response = []
    for row in ALL_STOCK_NUM_LIST:
        contract = token.Contracts.Stocks[row]
        if contract is None:
            ALL_STOCK_NUM_LIST.remove(row)
            logging.info('%s is no data', row)
            continue
        tmp = {
            'exchange': contract.exchange,
            'category': contract.category,
            'code': contract.code,
            'name': contract.name,
            'close': contract.reference,
            'updated': contract.update_date,
            'day_trade': contract.day_trade
        }
        response.append(tmp)
    if len(response) != 0:
        return jsonify(response)
    return jsonify({'status': 'fail'})


@ api.route('/pyapi/basic/update-basic', methods=['GET'])
def update_basic():
    ''' Update stock information
    ---
    tags:
      - basic
    responses:
      200:
        description: Success Response
      500:
        description: Server Not Ready
    '''
    try:
        subprocess.run(['./scripts/update_basic.sh'], check=True)
        fill_all_stock_list()
    except subprocess.CalledProcessError:
        connection_err()
        return jsonify({'status': 'fail'})
    return jsonify({'status': 'success'})


@ api.route('/pyapi/basic/update/snapshot', methods=['GET'])
def snapshot():
    ''' Get all stock latest volume and close
    ---
    tags:
      - data
    responses:
      200:
        description: Success Response
      500:
        description: Server Not Ready
    '''
    contracts = []
    contracts.append(token.Contracts.Indexs.TSE.TSE001)
    for stock in ALL_STOCK_NUM_LIST:
        contracts.append(token.Contracts.Stocks[stock])
    snapshots = token.snapshots(contracts)
    response = snapshot_pb2.SnapShotArrProto()
    for result in snapshots:
        tmp = snapshot_pb2.SnapShotProto()
        tmp.ts = result.ts
        tmp.code = result.code
        tmp.exchange = result.exchange
        tmp.open = result.open
        tmp.high = result.high
        tmp.low = result.low
        tmp.close = result.close
        tmp.tick_type = result.tick_type
        tmp.change_price = result.change_price
        tmp.change_rate = result.change_rate
        tmp.change_type = result.change_type
        tmp.average_price = result.average_price
        tmp.volume = result.volume
        tmp.total_volume = result.total_volume
        tmp.amount = result.amount
        tmp.total_amount = result.total_amount
        tmp.yesterday_volume = result.yesterday_volume
        tmp.buy_price = result.buy_price
        tmp.buy_volume = result.buy_volume
        tmp.sell_price = result.sell_price
        tmp.sell_volume = result.sell_volume
        tmp.volume_ratio = result.volume_ratio
        response.data.append(tmp)
    resp = make_response(response.SerializeToString())
    resp.headers['Content-Type'] = 'application/protobuf'
    return resp


@ api.route('/pyapi/history/entiretick', methods=['POST'])
def entiretick():
    ''' Get all history tick in one date
    ---
    tags:
      - data
    parameters:
      - in: body
        name: stock with date
        description: Stock with date
        required: true
        schema:
          $ref: '#/definitions/StockWithDate'
    responses:
      200:
        description: Success Response
      500:
        description: Server Not Ready
    definitions:
      StockWithDate:
        type: object
        properties:
          stock_num:
            type: string
          date:
            type: string
    '''
    response = entiretick_pb2.EntireTickArrProto()
    body = request.get_json()
    ticks = token.ticks(
        contract=token.Contracts.Stocks[body['stock_num']],
        date=body['date']
    )
    tmp_length = []
    total_count = len(ticks.ts)
    tmp_length.append(len(ticks.close))
    tmp_length.append(len(ticks.volume))
    tmp_length.append(len(ticks.bid_price))
    tmp_length.append(len(ticks.bid_volume))
    tmp_length.append(len(ticks.ask_price))
    tmp_length.append(len(ticks.ask_volume))
    for length in tmp_length:
        if length - total_count != 0:
            resp = make_response(response.SerializeToString())
            resp.headers['Content-Type'] = 'application/protobuf'
            return resp
    for pos in range(total_count):
        tmp = entiretick_pb2.EntireTickProto()
        tmp.ts = ticks.ts[pos]
        tmp.close = ticks.close[pos]
        tmp.volume = ticks.volume[pos]
        tmp.bid_price = ticks.bid_price[pos]
        tmp.bid_volume = ticks.bid_volume[pos]
        tmp.ask_price = ticks.ask_price[pos]
        tmp.ask_volume = ticks.ask_volume[pos]
        response.data.append(tmp)
    resp = make_response(response.SerializeToString())
    resp.headers['Content-Type'] = 'application/protobuf'
    return resp


@ api.route('/pyapi/history/kbar', methods=['POST'])
def fetch_kbar():
    ''' Get all kbar in date range
    ---
    tags:
      - data
    parameters:
      - in: body
        name: stock with date range
        description: Stock with date range
        required: true
        schema:
          $ref: '#/definitions/StockWithDateRange'
    responses:
      200:
        description: Success Response
      500:
        description: Server Not Ready
    definitions:
      StockWithDateRange:
        type: object
        properties:
          stock_num:
            type: string
          start_date:
            type: string
          end_date:
            type: string
    '''
    response = kbar_pb2.KbarArrProto()
    body = request.get_json()
    kbar = token.kbars(
        contract=token.Contracts.Stocks[body['stock_num']],
        start=body['start_date'],
        end=body['end_date'],
    )
    tmp_length = []
    total_count = len(kbar.ts)
    tmp_length.append(len(kbar.Close))
    tmp_length.append(len(kbar.Open))
    tmp_length.append(len(kbar.High))
    tmp_length.append(len(kbar.Low))
    tmp_length.append(len(kbar.Volume))
    for length in tmp_length:
        if length - total_count != 0:
            resp = make_response(response.SerializeToString())
            resp.headers['Content-Type'] = 'application/protobuf'
            return resp
    for pos in range(total_count):
        tmp = kbar_pb2.KbarProto()
        tmp.ts = kbar.ts[pos]
        tmp.Close = kbar.Close[pos]
        tmp.Open = kbar.Open[pos]
        tmp.High = kbar.High[pos]
        tmp.Low = kbar.Low[pos]
        tmp.Volume = kbar.Volume[pos]
        response.data.append(tmp)
    resp = make_response(response.SerializeToString())
    resp.headers['Content-Type'] = 'application/protobuf'
    return resp


@ api.route('/pyapi/history/tse_entiretick', methods=['POST'])
def tse_entiretick():
    ''' Get all tse tick in one date
    ---
    tags:
      - data
    parameters:
      - in: body
        name: fetch date
        description: fetch date
        required: true
        schema:
          $ref: '#/definitions/FetchDate'
    responses:
      200:
        description: Success Response
      500:
        description: Server Not Ready
    definitions:
      FetchDate:
        type: object
        properties:
          date:
            type: string
    '''
    response = entiretick_pb2.EntireTickArrProto()
    body = request.get_json()
    ticks = token.ticks(
        contract=token.Contracts.Indexs.TSE.TSE001,
        date=body['date']
    )
    tmp_length = []
    total_count = len(ticks.ts)
    tmp_length.append(len(ticks.close))
    tmp_length.append(len(ticks.volume))
    tmp_length.append(len(ticks.bid_price))
    tmp_length.append(len(ticks.bid_volume))
    tmp_length.append(len(ticks.ask_price))
    tmp_length.append(len(ticks.ask_volume))
    for length in tmp_length:
        if length - total_count != 0:
            resp = make_response(response.SerializeToString())
            resp.headers['Content-Type'] = 'application/protobuf'
            return resp
    for pos in range(total_count):
        tmp = entiretick_pb2.EntireTickProto()
        tmp.ts = ticks.ts[pos]
        tmp.close = ticks.close[pos]
        tmp.volume = ticks.volume[pos]
        tmp.bid_price = ticks.bid_price[pos]
        tmp.bid_volume = ticks.bid_volume[pos]
        tmp.ask_price = ticks.ask_price[pos]
        tmp.ask_volume = ticks.ask_volume[pos]
        response.data.append(tmp)
    resp = make_response(response.SerializeToString())
    resp.headers['Content-Type'] = 'application/protobuf'
    return resp


@ api.route('/pyapi/history/lastcount', methods=['POST'])
def lastcount():
    ''' Get stock's last count
    ---
    tags:
      - data
    parameters:
      - in: header
        name: X-Date
        description: Date
        required: true
      - in: body
        name: stock array
        description: Stock array
        required: true
        schema:
          $ref: '#/definitions/StockArr'
    responses:
      200:
        description: Success Response
      500:
        description: Server Not Ready
    definitions:
      StockArr:
        type: object
        properties:
          stock_num_arr:
            type: array
            items:
              $ref: '#/definitions/StockNum'
      StockNum:
          type: string
    '''
    date = request.headers['X-Date']
    body = request.get_json()
    stocks = body['stock_num_arr']
    response = []
    for stock in stocks:
        last_count = token.quote.ticks(
            contract=token.Contracts.Stocks[stock],
            date=date,
            query_type=sj.constant.TicksQueryType.LastCount,
            last_cnt=1,
        )
        tmp = {
            'date': date,
            'code': stock,
            'time': last_count.ts,
            'close': last_count.close,
        }
        response.append(tmp)
    if len(response) != 0:
        return jsonify(response)
    return jsonify({'status': 'fail'})


@ api.route('/pyapi/trade/volumerank', methods=['GET'])
def volumerank():
    ''' Get rank 200 volume and close
    ---
    tags:
      - data
    parameters:
      - in: header
        name: X-Count
        description: Count
        required: true
    responses:
      200:
        description: Success Response
      500:
        description: Server Not Ready
    '''
    rank_count = request.headers['X-Count']
    req_date = request.headers['X-Date']
    ranks = token.scanners(
        scanner_type=sj.constant.ScannerType.VolumeRank,
        count=rank_count,
        date=req_date,
    )
    response = volumerank_pb2.VolumeRankArrProto()
    for result in ranks:
        tmp = volumerank_pb2.VolumeRankProto()
        tmp.date = result.date
        tmp.code = result.code
        tmp.name = result.name
        tmp.ts = result.ts
        tmp.open = result.open
        tmp.high = result.high
        tmp.low = result.low
        tmp.close = result.close
        tmp.price_range = result.price_range
        tmp.tick_type = result.tick_type
        tmp.change_price = result.change_price
        tmp.change_type = result.change_type
        tmp.average_price = result.average_price
        tmp.volume = result.volume
        tmp.total_volume = result.total_volume
        tmp.amount = result.amount
        tmp.total_amount = result.total_amount
        tmp.yesterday_volume = result.yesterday_volume
        tmp.volume_ratio = result.volume_ratio
        tmp.buy_price = result.buy_price
        tmp.buy_volume = result.buy_volume
        tmp.sell_price = result.sell_price
        tmp.sell_volume = result.sell_volume
        tmp.bid_orders = result.bid_orders
        tmp.bid_volumes = result.bid_volumes
        tmp.ask_orders = result.ask_orders
        tmp.ask_volumes = result.ask_volumes
        response.data.append(tmp)
    resp = make_response(response.SerializeToString())
    resp.headers['Content-Type'] = 'application/protobuf'
    return resp


@ api.route('/pyapi/subscribe/bid-ask', methods=['POST'])
def bid_ask():
    ''' Subscribe bid-ask
    ---
    tags:
      - Subscribe bid-ask
    parameters:
      - in: body
        name: stock array
        description: Stock array
        required: true
        schema:
          $ref: '#/definitions/StockNumArr'
    responses:
      200:
        description: Success Response
      500:
        description: Server Not Ready
    definitions:
      StockNumArr:
        type: object
        properties:
          stock_num_arr:
            type: array
            items:
              $ref: '#/definitions/StockNum'
      StockNum:
        type: string
    '''
    body = request.get_json()
    stocks = body['stock_num_arr']
    for stock in stocks:
        BIDASK_SUB_LIST.append(stock)
        logging.info('subscribe bid-adk %s', stock)
        token.quote.subscribe(
            token.Contracts.Stocks[stock],
            quote_type=sj.constant.QuoteType.BidAsk,
            version=sj.constant.QuoteVersion.v1
        )
    return jsonify({'status': 'success'})


@ api.route('/pyapi/unsubscribe/bid-ask', methods=['POST'])
def un_bid_ask():
    ''' unSubscribe bid-ask
    ---
    tags:
      - Subscribe bid-ask
    parameters:
      - in: body
        name: stock array
        description: Stock array
        required: true
        schema:
          $ref: '#/definitions/StockNumArr'
    responses:
      200:
        description: Success Response
      500:
        description: Server Not Ready
    definitions:
      StockNumArr:
        type: object
        properties:
          stock_num_arr:
            type: array
            items:
              $ref: '#/definitions/StockNum'
      StockNum:
        type: string
    '''
    body = request.get_json()
    stocks = body['stock_num_arr']
    for stock in stocks:
        BIDASK_SUB_LIST.remove(stock)
        logging.info('unsubscribe bid-adk %s', stock)
        token.quote.unsubscribe(
            token.Contracts.Stocks[stock],
            quote_type=sj.constant.QuoteType.BidAsk,
            version=sj.constant.QuoteVersion.v1
        )
    return jsonify({'status': 'success'})


@ api.route('/pyapi/unsubscribeall/bid-ask', methods=['GET'])
def unstream_bid_ask_all():
    ''' Unubscribe all bid-ask
    ---
    tags:
      - Subscribe bid-ask
    responses:
      200:
        description: Success Response
      500:
        description: Server Not Ready
    '''
    global BIDASK_SUB_LIST  # pylint: disable=global-statement
    if len(BIDASK_SUB_LIST) != 0:
        for stock in BIDASK_SUB_LIST:
            logging.info('unsubscribe bid-adk %s', stock)
            token.quote.unsubscribe(
                token.Contracts.Stocks[stock],
                quote_type=sj.constant.QuoteType.BidAsk,
                version=sj.constant.QuoteVersion.v1
            )
        BIDASK_SUB_LIST = []
    return jsonify({'status': 'success'})


@ api.route('/pyapi/subscribe/streamtick', methods=['POST'])
def stream():
    ''' Subscribe streamtick
    ---
    tags:
      - Subscribe streamtick
    parameters:
      - in: body
        name: stock array
        description: Stock array
        required: true
        schema:
          $ref: '#/definitions/StockNumArr'
    responses:
      200:
        description: Success Response
      500:
        description: Server Not Ready
    '''
    body = request.get_json()
    stocks = body['stock_num_arr']
    for stock in stocks:
        QUOTE_SUB_LIST.append(stock)
        logging.info('subscribe stock %s', stock)
        token.quote.subscribe(
            token.Contracts.Stocks[stock],
            quote_type=sj.constant.QuoteType.Tick,
            version=sj.constant.QuoteVersion.v1
        )
    return jsonify({'status': 'success'})


@ api.route('/pyapi/unsubscribe/streamtick', methods=['POST'])
def un_stream():
    ''' unSubscribe streamtick
    ---
    tags:
      - Subscribe streamtick
    parameters:
      - in: body
        name: stock array
        description: Stock array
        required: true
        schema:
          $ref: '#/definitions/StockNumArr'
    responses:
      200:
        description: Success Response
      500:
        description: Server Not Ready
    '''
    body = request.get_json()
    stocks = body['stock_num_arr']
    for stock in stocks:
        QUOTE_SUB_LIST.remove(stock)
        logging.info('unsubscribe stock %s', stock)
        token.quote.unsubscribe(
            token.Contracts.Stocks[stock],
            quote_type=sj.constant.QuoteType.Tick,
            version=sj.constant.QuoteVersion.v1
        )
    return jsonify({'status': 'success'})


@ api.route('/pyapi/unsubscribeall/streamtick', methods=['GET'])
def unstream_all():
    ''' Unubscribe all streamtick
    ---
    tags:
      - Subscribe streamtick
    responses:
      200:
        description: Success Response
      500:
        description: Server Not Ready
    '''
    global QUOTE_SUB_LIST  # pylint: disable=global-statement
    if len(QUOTE_SUB_LIST) != 0:
        for stock in QUOTE_SUB_LIST:
            logging.info('unsubscribe stock %s', stock)
            token.quote.unsubscribe(
                token.Contracts.Stocks[stock],
                quote_type=sj.constant.QuoteType.Tick,
                version=sj.constant.QuoteVersion.v1
            )
        QUOTE_SUB_LIST = []
    return jsonify({'status': 'success'})


@ api.route('/pyapi/subscribe/future', methods=['POST'])
def sub_future():
    ''' Subscribe future
    ---
    tags:
      - Subscribe future
    parameters:
      - in: body
        name: future array
        description: future array
        required: true
        schema:
          $ref: '#/definitions/FutureNumArr'
    responses:
      200:
        description: Success Response
      500:
        description: Server Not Ready
    definitions:
      FutureNumArr:
        type: object
        properties:
          future_num_arr:
            type: array
            items:
              $ref: '#/definitions/FutureNum'
      FutureNum:
        type: string
    '''
    body = request.get_json()
    futures = body['future_num_arr']
    for future in futures:
        FUTURE_SUB_LIST.append(future)
        logging.info('subscribe future %s', future)
        token.quote.subscribe(
            token.Contracts.Futures[future],
            quote_type=sj.constant.QuoteType.Tick,
            version=sj.constant.QuoteVersion.v1
        )
    return jsonify({'status': 'success'})


@ api.route('/pyapi/unsubscribe/future', methods=['POST'])
def unsub_future():
    ''' unSubscribe future
    ---
    tags:
      - Subscribe future
    parameters:
      - in: body
        name: future array
        description: future array
        required: true
        schema:
          $ref: '#/definitions/FutureNumArr'
    responses:
      200:
        description: Success Response
      500:
        description: Server Not Ready
    '''
    body = request.get_json()
    futures = body['future_num_arr']
    for future in futures:
        FUTURE_SUB_LIST.remove(future)
        logging.info('unsubscribe future %s', future)
        token.quote.unsubscribe(
            token.Contracts.Futures[future],
            quote_type=sj.constant.QuoteType.Tick,
            version=sj.constant.QuoteVersion.v1
        )
    return jsonify({'status': 'success'})


@ api.route('/pyapi/unsubscribeall/future', methods=['GET'])
def unstream_all_future():
    ''' Unubscribe all future
    ---
    tags:
      - Subscribe future
    responses:
      200:
        description: Success Response
      500:
        description: Server Not Ready
    '''
    global FUTURE_SUB_LIST  # pylint: disable=global-statement
    if len(FUTURE_SUB_LIST) != 0:
        for future in FUTURE_SUB_LIST:
            logging.info('unsubscribe future %s', future)
            token.quote.unsubscribe(
                token.Contracts.Futures[future],
                quote_type=sj.constant.QuoteType.Tick,
                version=sj.constant.QuoteVersion.v1
            )
        FUTURE_SUB_LIST = []
    return jsonify({'status': 'success'})


@ api.route('/pyapi/system/restart', methods=['GET'])
def restart():
    ''' Restart
    ---
    tags:
      - system
    responses:
      200:
        description: Success Response
      500:
        description: Server Not Ready
    '''
    if deployment == 'docker':
        threading.Thread(target=run_pkill).start()
        return jsonify({'status': 'success'})
    return jsonify({'status': 'you should be in the docker container'})


@ api.route('/pyapi/system/tradebothost', methods=['POST'])
def set_trade_bot_host():
    ''' Set trade bot host
    ---
    tags:
      - system
    parameters:
      - in: header
        name: X-Trade-Bot-Host
        description: Trade bot host
        required: true
        schema:
          $ref: '#/definitions/TradeBotHost'
    responses:
      200:
        description: Success Response
      500:
        description: Server Not Ready
    definitions:
      TradeBotHost:
        type: string
    '''
    global TRADE_BOT_HOST  # pylint: disable=global-statement
    trade_bot_host = request.headers['X-Trade-Bot-Host']
    TRADE_BOT_HOST = trade_bot_host
    logging.warning('Change TRADE_BOT_HOST to %s', TRADE_BOT_HOST)
    return jsonify({'status': 'success'})


@ api.route('/pyapi/test/streamtick', methods=['POST'])
def test_streamtick():
    ''' Fake data for test
    ---
    tags:
      - fakedata
    parameters:
      - in: body
        name: count and time
        description: Count and Time
        required: true
        schema:
          $ref: '#/definitions/CountWithTotalTime'
    responses:
      200:
        description: Success Response
      500:
        description: Server Not Ready
    definitions:
      CountWithTotalTime:
        type: object
        properties:
          total_time:
            type: integer
          count:
            type: integer
      Date:
        type: string
    '''
    if TRADE_BOT_HOST == '':
        return jsonify({'status': 'TRADE_BOT_HOST is empty'})
    trade_bot_url = 'http://'+TRADE_BOT_HOST+':' + \
        trade_bot_port+'/trade-bot/data/target'
    body = request.get_json()
    req = session.get(trade_bot_url, headers={
        'Content-Type': 'application/json', 'count': body['count']})
    for data in req.json():
        threading.Thread(target=streamtick_fake_data, args=[
            data['stock_num'], data['close'], body['total_time']]).start()
    return jsonify({'status': 'success'})


@ api.route('/pyapi/trade/buy', methods=['POST'])
def buy():
    ''' Buy stock
    ---
    tags:
      - trade
    parameters:
      - in: body
        name: order
        description: Buy order
        required: true
        schema:
          $ref: '#/definitions/Order'
    responses:
      200:
        description: Success Response
      500:
        description: Server Not Ready
    definitions:
      Order:
        type: object
        properties:
          stock:
            type: string
          price:
            type: number
          quantity:
            type: integer
    '''
    body = request.get_json()
    contract = token.Contracts.Stocks[body['stock']]
    order = token.Order(
        price=body['price'],
        quantity=body['quantity'],
        action=sj.constant.Action.Buy,
        price_type=sj.constant.StockPriceType.LMT,
        order_type=sj.constant.TFTOrderType.ROD,
        order_lot=sj.constant.TFTStockOrderLot.Common,
        account=token.stock_account
    )
    trade = token.place_order(contract, order)
    if trade is not None and trade.order.id != '':
        if trade.status.status == constant.Status.Cancelled:
            trade.status.status = 'Canceled'
        return jsonify({
            'status': trade.status.status,
            'order_id': trade.order.id,
        })
    return jsonify({'status': 'fail'})


@ api.route('/pyapi/trade/sell_first', methods=['POST'])
def sell_first():
    ''' Sell stock first
    ---
    tags:
      - trade
    parameters:
      - in: body
        name: order
        description: Sell stock first
        required: true
        schema:
          $ref: '#/definitions/Order'
    responses:
      200:
        description: Success Response
      500:
        description: Server Not Ready
    definitions:
      Order:
        type: object
        properties:
          stock:
            type: string
          price:
            type: number
          quantity:
            type: integer
    '''
    body = request.get_json()
    contract = token.Contracts.Stocks[body['stock']]
    order = token.Order(
        price=body['price'],
        quantity=body['quantity'],
        action=sj.constant.Action.Sell,
        price_type=sj.constant.StockPriceType.LMT,
        order_type=sj.constant.TFTOrderType.ROD,
        order_lot=sj.constant.TFTStockOrderLot.Common,
        first_sell=sj.constant.StockFirstSell.Yes,
        account=token.stock_account
    )
    trade = token.place_order(contract, order)
    if trade is not None and trade.order.id != '':
        if trade.status.status == constant.Status.Cancelled:
            trade.status.status = 'Canceled'
        return jsonify({
            'status': trade.status.status,
            'order_id': trade.order.id,
        })
    return jsonify({'status': 'fail'})


@ api.route('/pyapi/trade/sell', methods=['POST'])
def sell():
    ''' Sell stock
    ---
    tags:
      - trade
    parameters:
      - in: body
        name: order
        description: Sell order
        required: true
        schema:
          $ref: '#/definitions/Order'
    responses:
      200:
        description: Success Response
      500:
        description: Server Not Ready
    definitions:
      Order:
        type: object
        properties:
          stock:
            type: string
          price:
            type: number
          quantity:
            type: integer
    '''
    body = request.get_json()
    contract = token.Contracts.Stocks[body['stock']]
    order = token.Order(
        price=body['price'],
        quantity=body['quantity'],
        action=sj.constant.Action.Sell,
        price_type=sj.constant.StockPriceType.LMT,
        order_type=sj.constant.TFTOrderType.ROD,
        order_lot=sj.constant.TFTStockOrderLot.Common,
        account=token.stock_account
    )
    trade = token.place_order(contract, order)
    if trade is not None and trade.order.id != '':
        if trade.status.status == constant.Status.Cancelled:
            trade.status.status = 'Canceled'
        return jsonify({
            'status': trade.status.status,
            'order_id': trade.order.id,
        })
    return jsonify({'status': 'fail'})


@ api.route('/pyapi/trade/cancel', methods=['POST'])
def cancel():
    ''' Cancel order
    ---
    tags:
      - trade
    parameters:
      - in: body
        name: order id
        description: Cancel Order ID
        required: true
        schema:
          $ref: '#/definitions/OrderID'
    responses:
      200:
        description: Success Response
      500:
        description: Server Not Ready
    definitions:
      OrderID:
        type: object
        properties:
          order_id:
            type: string
    '''
    cancel_order = None
    body = request.get_json()
    times = int()
    while True:
        token.update_status()
        orders = token.list_trades()
        for order in orders:
            if order.status.id == body['order_id']:
                cancel_order = order
        if cancel_order is not None or times >= 10:
            break
        times += 1
    if cancel_order is None:
        return jsonify({'status': 'not found'})
    if cancel_order.status.status == constant.Status.Cancelled:
        return jsonify({'status': 'already'})
    token.cancel_order(cancel_order)
    times = 0
    while True:
        if times >= 10:
            break
        token.update_status()
        orders = token.list_trades()
        for order in orders:
            if order.status.id == body['order_id'] and order.status.status == constant.Status.Cancelled:
                return jsonify({'status': 'success'})
        times += 1
    return jsonify({'status': 'fail'})


@ api.route('/pyapi/trade/history', methods=['GET'])
def trade_history():
    ''' Order history
    ---
    tags:
      - trade
    responses:
      200:
        description: Success Response
      500:
        description: Server Not Ready
    '''
    response = []
    token.update_status()
    orders = token.list_trades()
    if len(orders) == 0:
        return jsonify({'status': 'not found', 'orders': response, })
    for order in orders:
        tmp = {
            'status': order.status.status,
            'code': order.contract.code,
            'action': order.order.action,
            'price': order.order.price,
            'quantity': order.order.quantity,
            'order_id': order.order.id,
            'order_time': datetime.strftime(order.status.order_datetime, '%Y-%m-%d %H:%M:%S')
        }
        response.append(tmp)
    return jsonify({'status': 'success', 'orders': response, })


@ api.route('/pyapi/trade/status', methods=['GET'])
def status():
    ''' Get order status
    ---
    tags:
      - status
    responses:
      200:
        description: Success Response
      500:
        description: Server Not Ready
    '''
    try:
        token.update_status(timeout=0, cb=status_callback)
    except error.TokenError:
        send_token_expired_event()
        threading.Thread(target=run_pkill).start()
    return jsonify({'status': 'success'})


def status_callback(reply: typing.List[sj.order.Trade]):
    '''Sinopac status's callback.'''
    result = traderecord_pb2.TradeRecordArrProto()
    if len(reply) != 0:
        for order in reply:
            res = traderecord_pb2.TradeRecordProto()
            if order.status.status == constant.Status.Cancelled:
                order.status.status = 'Canceled'
            if order.status.order_datetime is None:
                order.status.order_datetime = datetime.now()
            res.code = order.contract.code
            res.action = order.order.action
            res.price = order.order.price
            res.quantity = order.order.quantity
            res.id = order.status.id
            res.status = order.status.status
            res.order_time = datetime.strftime(
                order.status.order_datetime, '%Y-%m-%d %H:%M:%S')
            result.data.append(res)
        send_trade_record(result.SerializeToString())


def quote_callback_v1(exchange: Exchange, tick: TickSTKv1):
    '''Sinopac's quiote callback v1.'''
    if TRADE_BOT_HOST == '':
        logging.warning('TRADE_BOT_HOST is empty, quote_callback_v1')
        return
    trade_bot_url = 'http://'+TRADE_BOT_HOST+':' + \
        trade_bot_port+'/trade-bot/data/streamtick'
    res = streamtick_pb2.StreamTickProto()
    res.exchange = exchange
    res.tick.code = tick.code
    res.tick.date_time = datetime.strftime(
        tick.datetime, '%Y-%m-%d %H:%M:%S.%f')
    res.tick.open = tick.open
    res.tick.avg_price = tick.avg_price
    res.tick.close = tick.close
    res.tick.high = tick.high
    res.tick.low = tick.low
    res.tick.amount = tick.amount
    res.tick.total_amount = tick.total_amount
    res.tick.volume = tick.volume
    res.tick.total_volume = tick.total_volume
    res.tick.tick_type = tick.tick_type
    res.tick.chg_type = tick.chg_type
    res.tick.price_chg = tick.price_chg
    res.tick.pct_chg = tick.pct_chg
    res.tick.bid_side_total_vol = tick.bid_side_total_vol
    res.tick.ask_side_total_vol = tick.ask_side_total_vol
    res.tick.bid_side_total_cnt = tick.bid_side_total_cnt
    res.tick.ask_side_total_cnt = tick.ask_side_total_cnt
    res.tick.suspend = tick.suspend
    res.tick.simtrade = tick.simtrade
    try:
        session.post(trade_bot_url, headers={
            'Content-Type': 'application/protobuf'}, data=res.SerializeToString(), timeout=20)
    except requests.exceptions.ConnectionError:
        connection_err()
        logging.error('quote callback err: %s, %s', tick.code,
                      datetime.strftime(tick.datetime, '%Y-%m-%d %H:%M:%S.%f'))
        return


def bid_ask_callback(exchange: Exchange, bidask: BidAskSTKv1):
    '''Sinopac's bidask callback.'''
    if TRADE_BOT_HOST == '':
        logging.warning('TRADE_BOT_HOST is empty, bid_ask_callback')
        return
    trade_bot_url = 'http://'+TRADE_BOT_HOST+':' + \
        trade_bot_port+'/trade-bot/data/bid-ask'
    res = bidask_pb2.BidAskProto()
    res.exchange = exchange
    res.bid_ask.code = bidask.code
    res.bid_ask.date_time = datetime.strftime(
        bidask.datetime, '%Y-%m-%d %H:%M:%S.%f')
    res.bid_ask.bid_price.extend(bidask.bid_price)
    res.bid_ask.bid_volume.extend(bidask.bid_volume)
    res.bid_ask.diff_bid_vol.extend(bidask.diff_bid_vol)
    res.bid_ask.ask_price.extend(bidask.ask_price)
    res.bid_ask.ask_volume.extend(bidask.ask_volume)
    res.bid_ask.diff_ask_vol.extend(bidask.diff_ask_vol)
    res.bid_ask.suspend = bidask.suspend
    res.bid_ask.simtrade = bidask.simtrade
    try:
        session.post(trade_bot_url, headers={
            'Content-Type': 'application/protobuf'}, data=res.SerializeToString(), timeout=20)
    except requests.exceptions.ConnectionError:
        connection_err()
        logging.error('bidask callback err: %s, %s', bidask.code,
                      datetime.strftime(bidask.datetime, '%Y-%m-%d %H:%M:%S.%f'))
        return


def event_callback(resp_code: int, event_code: int, info: str, event: str):
    '''Sinopac's event callback.'''
    if TRADE_BOT_HOST == '':
        logging.warning('TRADE_BOT_HOST is empty, event_callback')
        return
    trade_bot_url = 'http://'+TRADE_BOT_HOST+':' + \
        trade_bot_port+'/trade-bot/trade-event'
    res = tradeevent_pb2.EventProto()
    res.resp_code = resp_code
    res.event_code = event_code
    res.info = info
    res.event = event
    try:
        session.post(trade_bot_url, headers={
            'Content-Type': 'application/protobuf'}, data=res.SerializeToString(), timeout=20)
    except requests.exceptions.ConnectionError:
        connection_err()
        logging.error('event callback err: %d, %d, %s, %s',
                      resp_code, event_code, info, event)
        return


def fill_all_stock_list():
    '''Fill ALL_STOCK_NUM_LIST'''
    global ALL_STOCK_NUM_LIST  # pylint: disable=global-statement
    ALL_STOCK_NUM_LIST = []
    with open('./data/stock_tse.csv', newline='', encoding='utf-8') as csvfile:
        rows = csv.reader(csvfile)
        for row in rows:
            if row[1] == '公司代號':
                continue
            ALL_STOCK_NUM_LIST.append(row[1])
    with open('./data/stock_otc.csv', newline='', encoding='utf-8') as csvfile:
        rows = csv.reader(csvfile)
        for row in rows:
            if row[1] == '公司代號':
                continue
            ALL_STOCK_NUM_LIST.append(row[1])


def run_pkill():
    '''Restart in container'''
    time.sleep(1)
    os._exit(0)  # pylint: disable=protected-access


def streamtick_fake_data(stock_num: str, close: float, total_time: int):
    '''Fake Data generator'''
    if TRADE_BOT_HOST == '':
        logging.warning('TRADE_BOT_HOST is empty, streamtick_fake_data')
        return
    trade_bot_url = 'http://'+TRADE_BOT_HOST+':' + \
        trade_bot_port+'/trade-bot/data/streamtick'
    logging.info('ticking %s %f', stock_num, close)
    for _ in range(total_time*10):
        res = streamtick_pb2.StreamTickProto()
        res.exchange = 'exchange test'
        res.tick.code = stock_num
        res.tick.date_time = datetime.strftime(
            datetime.now(), '%Y-%m-%d %H:%M:%S.%f')
        res.tick.open = close
        res.tick.avg_price = close
        res.tick.close = close
        res.tick.high = close
        res.tick.low = close
        res.tick.amount = 60000
        res.tick.total_amount = 60000000
        res.tick.volume = 100
        res.tick.total_volume = 2000
        res.tick.tick_type = 1
        res.tick.chg_type = 1
        res.tick.price_chg = 0
        res.tick.pct_chg = 0
        res.tick.bid_side_total_vol = 100
        res.tick.ask_side_total_vol = 5000
        res.tick.bid_side_total_cnt = 200
        res.tick.ask_side_total_cnt = 200
        res.tick.suspend = 0
        res.tick.simtrade = 0
        try:
            session.post(trade_bot_url, headers={
                'Content-Type': 'application/protobuf'}, data=res.SerializeToString(), timeout=20)
        except requests.exceptions.ConnectionError:
            connection_err()
            logging.error('fake stream data err: %s, %f, %d',
                          stock_num, close, total_time)
            return


def send_trade_record(record):
    '''Sinopac status's callback.'''
    if TRADE_BOT_HOST == '':
        logging.warning('TRADE_BOT_HOST is empty, send_trade_record')
        return
    trade_bot_url = 'http://'+TRADE_BOT_HOST+':' + \
        trade_bot_port+'/trade-bot/trade-record'
    try:
        session.post(trade_bot_url, headers={
            'Content-Type': 'application/protobuf'}, data=record, timeout=20)
    except requests.exceptions.ConnectionError:
        connection_err()
        logging.error('send trade record err: %s', record)
        return


def send_token_expired_event():
    '''Sinopac's event callback.'''
    if TRADE_BOT_HOST == '':
        logging.warning('TRADE_BOT_HOST is empty, send_token_expired_event')
        return
    trade_bot_url = 'http://'+TRADE_BOT_HOST+':' + \
        trade_bot_port+'/trade-bot/trade-event'
    res = tradeevent_pb2.EventProto()
    res.resp_code = 500
    res.event_code = 401
    res.info = 'Please resubscribe if there exits subscription'
    res.event = 'Token is expired.'
    try:
        session.post(trade_bot_url, headers={
            'Content-Type': 'application/protobuf'}, data=res.SerializeToString(), timeout=20)
    except requests.exceptions.ConnectionError:
        connection_err()
        logging.error('send token expired event err')
        return


def connection_err():
    '''Error counter.'''
    global ERROR_TIMES  # pylint: disable=global-statement
    ERROR_TIMES += 1
    if ERROR_TIMES > 30:
        threading.Thread(target=run_pkill).start()


def reset_err():
    '''Error reset.'''
    global ERROR_TIMES  # pylint: disable=global-statement
    record = int()
    while True:
        if ERROR_TIMES == record and record > 0:
            logging.warning('%d error reset', ERROR_TIMES)
            ERROR_TIMES = 0
        record = ERROR_TIMES
        time.sleep(30)


def place_order_callback(order_state: constant.OrderState, order: dict):
    '''Place order callback'''
    if search('DEAL', order_state) is None:
        logging.info('Order: %s %s %s %s %s %s %.2f %d %d %s',
                     order_state,
                     order['operation']['op_type'],
                     order['operation']['op_code'],
                     order['operation']['op_msg'],
                     order['order']['id'],
                     order['order']['action'],
                     order['order']['price'],
                     order['order']['quantity'],
                     order['status']['exchange_ts'],
                     order['contract']['code'],
                     )
    else:
        logging.info('Deal: %s %s %s %s %s %.2f %d %d',
                     order_state,
                     order['trade_id'],
                     order['exchange_seq'],
                     order['action'],
                     order['code'],
                     order['price'],
                     order['quantity'],
                     order['ts'],
                     )


def future_quote_callback(exchange: Exchange, tick: TickFOPv1):
    logging.info(exchange)
    logging.info(tick)


def login_callback(security_type: constant.SecurityType):
    '''login event callback.'''
    with mutex:
        global SERVER_STATUS  # pylint: disable=global-statement
        if security_type.value in ('STK', 'IND', 'FUT', 'OPT'):
            SERVER_STATUS += 1
            logging.warning('login step: %d/4, %s',
                            SERVER_STATUS, security_type)


def sino_login():
    '''Login into Sinopac'''
    token.login(
        person_id=TRADE_ID,
        passwd=TRADE_PASSWD,
        contracts_cb=login_callback
    )
    token.set_order_callback(place_order_callback)
    token.quote.set_event_callback(event_callback)
    token.quote.set_on_tick_stk_v1_callback(quote_callback_v1)
    token.quote.set_on_bidask_stk_v1_callback(bid_ask_callback)
    token.quote.set_on_tick_fop_v1_callback(future_quote_callback)
    while True:
        if SERVER_STATUS == 4:
            break
    token.activate_ca(
        ca_path='./data/ca_sinopac.pfx',
        ca_passwd=CA_PASSWD,
        person_id=TRADE_ID,
    )


@ api.route('/pyapi/trade/logout', methods=['GET'])
def sino_logout():
    ''' Shioaji logout
    ---
    tags:
      - status
    responses:
      200:
        description: Success Response
      500:
        description: Server Not Ready
    '''
    global SERVER_STATUS  # pylint: disable=global-statement
    token.logout()
    SERVER_STATUS = 0
    return jsonify({'status': 'success'})


@ api.route('/pyapi/system/healthcheck', methods=['GET'])
def health_check():
    ''' Server health check
    ---
    tags:
      - system
    responses:
      200:
        description: Success Response
      500:
        description: Server Not Ready
    '''
    return jsonify({
        'status': 'success',
        'up_time_min': UP_TIME,
    })


def sino_re_login():
    '''Shioaji re login'''
    global SERVER_STATUS, RE_LOGGING  # pylint: disable=global-statement
    RE_LOGGING = True
    token.logout()
    SERVER_STATUS = 0
    sino_login()
    RE_LOGGING = False
    return jsonify({'status': 'success'})


def check_login_status():
    '''API interceptor'''
    if SERVER_STATUS != 4:
        logging.warning('shioaji not ready')
        if RE_LOGGING is False:
            sino_re_login()
            return None
        resp = make_response({'status': 'shioaji not ready'}, 500)
        return resp
    return None


def server_up_time():
    '''Record server up time'''
    global UP_TIME  # pylint: disable=global-statement
    while True:
        time.sleep(60)
        UP_TIME += 1


if __name__ == '__main__':
    fill_all_stock_list()
    threading.Thread(target=reset_err).start()
    threading.Thread(target=server_up_time).start()
    sino_login()
    api.before_request(check_login_status)
    serve(api, host='0.0.0.0', port=sys.argv[1])
