#!/usr/bin/env python3

import asyncio
from datetime import datetime
import sys
import json
from copra.websocket import Channel, Client
from pprint import pprint

bestbid = bestask = legitvol = fakevol = 0
bidsd = {}
asksd = {}
change = 0

def dicttofloat(keyvalue):
        return float(keyvalue[0])

class Ticker(Client):
    def on_message(self, message):
        global bestbid, bestask, legitvol, fakevol, asks, bids, asksd, bidsd, change
        if message['type'] == 'snapshot':
            #print(message)
            bids=message['bids']

            for el in bids:
                bidsd[ float(el[0]) ] = el[1]
            k=sorted(bidsd.keys(), reverse = True)
            bestbid=k[0]
            asks=message['asks']
            for l3 in asks:
                asksd[ float(l3[0]) ] = l3[1]
            l=sorted(asksd.keys())
            bestask=l[0]                   
            #pprint(bids)
            #pprint(bidsd)
            #pprint(asksd)

            print("Best bid: $" + str(bestbid) + ", Best offer: $" + str(bestask))
        elif message['type'] == 'l2update':
            timestamp=message['time']
            side=message['changes'][0][0]
            price=float(message['changes'][0][1])
            qty=float(message['changes'][0][2])
            #print(message['changes'])
            if message['changes'][0][0] == 'buy':
                if qty!=0.0:
                    bidsd.update({price:qty})
                else:
                    bidsd.pop(price)

                k=sorted(bidsd.keys(), reverse=True)
                bestbid=k[0]
                #print(bidsd.get(price))
                #for k in sorted (bidsd, reverse=True):
                #   print((k, bidsd[k]), end = " ")
            if message['changes'][0][0] == 'sell':
                if qty!=0.0:
                    asksd.update({price:qty})
                else:
                    asksd.pop(price)
                l=sorted(asksd.keys())
                bestask=l[0]
            if bestask <= bestbid:
                print("########################## BOOK CROSS ################")
            else:

                print('\u001b[38;5;244m', timestamp, '\u001b[38;5;83m', bestbid, '\033[0m', '\u001b[38;5;244m', '----', '\033[0m', '\u001b[38;5;196m', bestask, '\033[0m')

                print('\033[95m', 'total fake: ', fakevol, ' BTC', '\033[0m')
                print('\033[95m', 'total legit: ', legitvol, ' BTC', '\033[0m')

        elif message['type'] == 'match':
            timestamp=message['time']
            price=float(message['price'])
            qty=float(message['size'])
            if price>bestbid and price<bestask:
                fakevol=fakevol+qty
                print('\033[93m', '-- EXECUTION BETWEEN SPREAD (_o_): ', price, 'for', qty, '\033[0m')
            else:
                legitvol=legitvol+qty
                print('\u001b[38;5;244m', '-- Legit Trade: ', price, 'for', qty, '\033[0m')

            print('\033[95m', 'total fake: ', fakevol, ' BTC', '\033[0m')
            print('\033[95m', 'total legit: ', legitvol, ' BTC', '\033[0m')
            #match = Match(message)
            #print(tick, "\n\n")

product_id = "BTC-USD"

loop = asyncio.get_event_loop()

channelt = Channel('level2', product_id)
channelm = Channel('matches', product_id)

ticker = Ticker(loop, channelt)
ticker = Ticker(loop, channelm)

try:
    loop.run_forever()
except KeyboardInterrupt:
    loop.run_until_complete(ticker.close())
    loop.close()
