#!/usr/bin/env python

import sys
import json
import signal
from websocket import create_connection
from volumne_analyser import VolumeAnalyser
from pprint import pprint
from datetime import datetime 

if __name__ == "__main__":

	va = VolumeAnalyser('FTX')
	va.set_symbol_info( { 'symbol': 'BTC-PERP', 'base_asset': 'BTC', 'quote_asset': 'USD'} ) 
	bestbid = bestask = legitvol = fakevol = num_fake_trades = num_legit_trades= 0
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
				va.bestbid=k[0]
				asks=api_data['data']['asks']
				for l3 in asks:
					asksd[ float(l3[0]) ] = l3[1]
				l=sorted(asksd.keys())
				va.bestoffer=l[0]    

				data = {
					'u' : float(api_data['data']['time']), # Unique, order book updateId
					'bb': float(va.bestbid),  # best bid 
					'bo': float(va.bestoffer), # best offer
					'bq': float(0), # best bid qty
					'aq': float(0), # best ask qty
				}
				va.process_book_entry(data)

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
				va.bestbid=k[0]
				if asks:
					for el in asks:
						price=float(el[0])
						qty=float(el[1])
						if qty!=0.0:
							asksd.update({price:qty})
						else:
							asksd.pop(price)
				k=sorted(asksd.keys())
				va.bestoffer=k[0]			
				
				data = {
					'u' : float(api_data['data']['time']), # Unique, order book updateId
					'bb': float(va.bestbid),  # best bid 
					'bo': float(va.bestoffer), # best offer
					'bq': float(0), # best bid qty
					'aq': float(0), # best ask qty
				}
				va.process_book_entry(data)


				# print("Best bid: $" + str(bestbid) + ", Best offer: $" + str(bestask))
			elif api_data['channel'] == 'trades' and api_data['type'] == 'update':

				trades=api_data['data']
				for trade in trades:

					ts = datetime.strptime(trade['time'][:-6], "%Y-%m-%dT%H:%M:%S.%f")
					ts_milis = (ts - datetime.utcfromtimestamp(0)).total_seconds() * 1000 

					data = { 
						'ts': float(ts_milis),
						'price': float(trade['price']),
						'qty': float(trade['size']),
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
