#!/usr/bin/env python

import sys
import json
import signal
from websocket import create_connection

bestbid = bestask = legitvol = fakevol = num_fake_trades = num_legit_trades = 0
bidsd = {}
asksd = {}
api_domain = "wss://ws.bitstamp.net"

try:
	ws = create_connection(api_domain)
except Exception as error:
	print("WebSocket connection failed (%s)" % error)
	sys.exit(1)

ws.send(json.dumps({
	"event": "bts:subscribe",
	"data": {
		"channel": "order_book_btcusd" 
}
}))

ws.send(json.dumps({
	"event": "bts:subscribe",
	"data": {
		"channel": "live_trades_btcusd" 
}
}))


while True:
	try:
		api_data = ws.recv()
		api_data=json.loads(api_data)
		#print(api_data)
		if api_data['channel'] == 'order_book_btcusd' and api_data['event'] == 'data':
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
			#print(l) 
			print('\u001b[38;5;83m', bestbid, '\033[0m', '\u001b[38;5;244m', '----', '\033[0m', '\u001b[38;5;196m', bestask, '\033[0m')
			# print("Best bid: $" + str(bestbid) + ", Best offer: $" + str(bestask))
		elif api_data['channel'] == 'live_trades_btcusd' and api_data['event'] == 'trade':
			qty=float(api_data['data']['amount'])
			price=float(api_data['data']['price'])
			if price>bestbid and price<bestask:
				fakevol=fakevol+qty
				num_fake_trades = num_fake_trades + 1
				# print("- FAKE match of " + str(qty) + " BTC at $" + str(price))
				print('\033[93m', '-- EXECUTION BETWEEN SPREAD (_o_): ', price, 'for', qty, '\033[0m')
			else:
				legitvol=legitvol+qty
				num_legit_trades = num_legit_trades + 1
				print('\u001b[38;5;244m', '-- Legit Trade: ', price, 'for', qty, '\033[0m')
				# print("- LEGIT match of " + str(qty) + " BTC at $" + str(price))

			print('\033[95m', 'total fake: ', fakevol, ' BTC', '\033[0m')
			print('\033[95m', 'total legit: ', legitvol, ' BTC', '\033[0m')
			print('\033[95m', 'total fake trades: ', num_fake_trades, '\033[0m')
			print('\033[95m', 'total legit trades: ', num_legit_trades, '\033[0m')


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
