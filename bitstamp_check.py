#!/usr/bin/env python

import sys
import json
import signal
from websocket import create_connection
from volumne_analyser import VolumeAnalyser
from pprint import pprint

if __name__ == "__main__":


	va = VolumeAnalyser('Bitstamp', output_print=True)
	bestbid = bestask = legitvol = fakevol = num_fake_trades = num_legit_trades = 0
	bidsd = {}
	asksd = {}
	last_update = 0
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
				va.bestbid=k[0]
				asks=api_data['data']['asks']
				for l3 in asks:
					asksd[ float(l3[0]) ] = l3[1]
				l=sorted(asksd.keys())
				va.bestoffer=l[0]    
				#print(l) 

				data = {
					'u' : int(api_data['data']['microtimestamp']), # Unique, order book updateId
					'bb': float(va.bestbid),  # best bid 
					'bo': float(va.bestoffer), # best offer
					'bq': float(0), # best bid qty
					'aq': float(0), # best ask qty
				}
				va.process_book_entry(data)

			elif api_data['channel'] == 'live_trades_btcusd' and api_data['event'] == 'trade':

				data = { 
					'ts': int(api_data['data']['microtimestamp']),
					'price': float(api_data['data']['price']),
					'qty': float(api_data['data']['amount']),
				}
				va.process_trade_entry(data) 
				va.print_summary()


		except KeyboardInterrupt:
			ws.close()
			sys.exit(0)
		except Exception as error:
			print("WebSocket message failed (%s)" % error)
			ws.close()
			sys.exit(1)

	ws.close()
	sys.exit(1)
