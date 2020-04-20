#!/usr/bin/env python

import sys
import json
import signal
from websocket import create_connection
from volumne_analyser import VolumeAnalyser
from pprint import pprint
from datetime import datetime 


if __name__ == "__main__":

	#validates volume on Kraken's XBT/EUR pair
	global dabestbid, dabestask, last_book_update, va 
	va = VolumeAnalyser('Kraken', output_print=True)
	dabestbid = dabestask = last_book_update = 0

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
		bestbid=round(float(best_bid()),1)
		bestask=round(float(best_ask()),1)
		pprint(last_book_update)

		data = {
			'u' : float(last_book_update), # Unique, order book updateId
			'bb': float(va.bestbid),  # best bid 
			'bo': float(va.bestoffer), # best offer
			'bq': float(0), # best bid qty
			'aq': float(0), # best ask qty
		}
		va.process_book_entry(data)

	def api_update_book(side, data):

		for x in data:
			price_level = x[0]
			last_book_update = x[2]
			if float(x[1]) != 0.0:
				api_book[side].update({price_level:float(x[1])})
			else:
				if price_level in api_book[side]:
					api_book[side].pop(price_level)
		if side == "bid":
			api_book["bid"] = dict(sorted(api_book["bid"].items(), key=dicttofloat, reverse=True)[:int(api_depth)])
		elif side == "ask":
			api_book["ask"] = dict(sorted(api_book["ask"].items(), key=dicttofloat)[:int(api_depth)])

		pprint(last_book_update)



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

	totalfake = totallegit = num_fake_trades = num_legit_trades = 0

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
				va.bestbid=round(float(best_bid()),1)
				va.bestoffer=round(float(best_ask()),1)
				trade_ts = result[1][0][2]

				data = { 
					'ts': float(trade_ts),
					'price': float(tradeprice),
					'qty': float(tradevol),
				}
				va.process_trade_entry(data) 
				va.print_summary()



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
