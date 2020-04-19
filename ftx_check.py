#!/usr/bin/env python

import sys
import json
import signal
from websocket import create_connection

bestbid = bestask = legitvol = fakevol = 0
bidsd = {}
asksd = {}
api_domain = "wss://ftx.com/ws/"

try:
	ws = create_connection(api_domain)
except Exception as error:
	print("WebSocket connection failed (%s)" % error)
	sys.exit(1)

ws.send(json.dumps({
	"op": "subscribe",
	"channel": "trades",
	"market": "BTC-PERP" 
}))

ws.send(json.dumps({
	"op": "subscribe",
	"channel": "orderbook",
	"market": "BTC-PERP" 
}))


while True:
	try:
		api_data = ws.recv()
		api_data=json.loads(api_data)
		#print(api_data)
		if api_data['channel'] == 'orderbook' and api_data['type'] == 'partial':
			bids=api_data['data']['bids']
			for el in bids:
				bidsd[ float(el[0]) ] = el[1]
			k=sorted(bidsd.keys(), reverse = True)
			bestbid=k[0]
			asks=api_data['data']['asks']
			for l3 in asks:
				asksd[ float(l3[0]) ] = l3[1]
			l=sorted(asksd.keys())
			bestask=l[0]    
			# print(l)    
			# print("Best bid: $" + str(bestbid) + ", Best offer: $" + str(bestask))
			print('\u001b[38;5;83m', bestbid, '\033[0m', '\u001b[38;5;244m', '----', '\033[0m', '\u001b[38;5;196m', bestask, '\033[0m')
		elif api_data['channel'] == 'orderbook' and api_data['type'] == 'update':
			bids=api_data['data']['bids']
			asks=api_data['data']['asks']
			
			if bids:
				for el in bids:
					price=float(el[0])
					qty=float(el[1])
					if qty!=0.0:
						bidsd.update({price:qty})
					else:
						bidsd.pop(price)
			k=sorted(bidsd.keys(), reverse=True)
			bestbid=k[0]
			if asks:
				for el in asks:
					price=float(el[0])
					qty=float(el[1])
					if qty!=0.0:
						asksd.update({price:qty})
					else:
						asksd.pop(price)
			k=sorted(asksd.keys())
			bestask=k[0]			
			print('\u001b[38;5;83m', bestbid, '\033[0m', '\u001b[38;5;244m', '----', '\033[0m', '\u001b[38;5;196m', bestask, '\033[0m')
			# print("Best bid: $" + str(bestbid) + ", Best offer: $" + str(bestask))
		elif api_data['channel'] == 'trades' and api_data['type'] == 'update':
			trades=api_data['data']
			for trade in trades:
				qty=float(trade['size'])
				price=float(trade['price'])
				if price>bestbid and price<bestask:
					fakevol=fakevol+qty
					print('\033[93m', '-- EXECUTION BETWEEN SPREAD (_o_): ', price, 'for', qty, '\033[0m')
					# print("- FAKE match of " + str(qty) + " BTC at $" + str(price))
				else:
					legitvol=legitvol+qty
					print('\u001b[38;5;244m', '-- Legit Trade: ', price, 'for', qty, '\033[0m')
					# print("- LEGIT match of " + str(qty) + " BTC at $" + str(price))
			print('\033[95m', 'total fake: ', fakevol, ' BTC', '\033[0m')
			print('\033[95m', 'total legit: ', legitvol, ' BTC', '\033[0m')
			# print("Total fake: " + str(fakevol) + " BTC, legit: " + str(legitvol) + " BTC")

	except KeyboardInterrupt:
		ws.close()
		sys.exit(0)
	except Exception as error:
		print("WebSocket message failed (%s)" % error)
		ws.close()
		sys.exit(1)

ws.close()
sys.exit(1)