#!/usr/bin/env python

import sys
import json
import signal
from websocket import create_connection

#validates volume on Kraken's XBT/EUR pair
global dabestbid, dabestask
dabestbid = dabestask = 0
def dicttofloat(keyvalue):
        return float(keyvalue[0])

def best_bid():
	bid = sorted(api_book["bid"].items(), key=dicttofloat, reverse=True)
	return bid[0][0]
	
def best_ask():
	ask = sorted(api_book["ask"].items(), key=dicttofloat)
	return ask[0][0]	

def printfunction(signalnumber, frame):
	signal.alarm(1)
	thebestbid=round(float(best_bid()),1)
	thebestask=round(float(best_ask()),1)
	print("Best bid: €" + str(thebestbid) + ", best offer: €" + str(thebestask))

def api_update_book(side, data):
	for x in data:
		price_level = x[0]
		if float(x[1]) != 0.0:
			api_book[side].update({price_level:float(x[1])})
		else:
			if price_level in api_book[side]:
				api_book[side].pop(price_level)
	if side == "bid":
		api_book["bid"] = dict(sorted(api_book["bid"].items(), key=dicttofloat, reverse=True)[:int(api_depth)])
	elif side == "ask":
		api_book["ask"] = dict(sorted(api_book["ask"].items(), key=dicttofloat)[:int(api_depth)])

signal.signal(signal.SIGALRM, printfunction)

api_feed = "book"
api_symbol = "XBT/EUR"
api_depth = 10
api_domain = "wss://ws.kraken.com/"
api_book = {"bid":{}, "ask":{}}

try:
	ws = create_connection(api_domain)
except Exception as error:
	print("WebSocket connection failed (%s)" % error)
	sys.exit(1)

api_data = '{"event":"subscribe", "subscription":{"name":"%(feed)s", "depth":%(depth)s}, "pair":["%(symbol)s"]}' % {"feed":api_feed, "depth":api_depth, "symbol":api_symbol}

ws.send(json.dumps({
	"event": "subscribe",
	"pair": ["XBT/EUR"],
	"subscription": {"name": "trade" }
}))

try:
	ws.send(api_data)
except Exception as error:
	print("Feed subscription failed (%s)" % error)
	ws.close()
	sys.exit(1)

totalfake = totallegit = 0

while True:
	try:
		api_data = ws.recv()
	except KeyboardInterrupt:
		ws.close()
		sys.exit(0)
	except Exception as error:
		print("WebSocket message failed (%s)" % error)
		ws.close()
		sys.exit(1)
	api_data = json.loads(api_data)
	result=api_data
	if type(api_data) == list:
		if str(api_data[0]) == '241':
			tradeprice=float(result[1][0][0])
			tradevol=result[1][0][0]
			bestbid=round(float(best_bid()),1)
			bestask=round(float(best_ask()),1)
			print("Best bid: €" + str(bestbid) + ", Best ask: €" + str(bestask))
			vol=round(float(result[1][0][1]),4)
			if tradeprice<float(bestask) and tradeprice>float(bestbid):
				totalfake=round(totalfake+vol,4)
				print("FAKE trade of " + str(vol) + "XBT at price €" + str(result[1][0][0]))
			else:
				totallegit=round(totallegit+vol,4)
				print("LEGIT trade of " + str(vol) + "XBT at price €" + str(result[1][0][0]))
			print("Total fake: " + str(totalfake) + " XBT, legit: " + str(totallegit) + "XBT")
		elif "as" in api_data[1]:
			api_update_book("ask", api_data[1]["as"])
			api_update_book("bid", api_data[1]["bs"])
			signal.alarm(1)
		elif "a" in api_data[1] or "b" in api_data[1]:
			for x in api_data[1:len(api_data[1:])-1]:
				if "a" in x:
					api_update_book("ask", x["a"])
				elif "b" in x:
					api_update_book("bid", x["b"])

ws.close()
sys.exit(1)