from volumne_analyser import VolumeAnalyser


import asyncio
from copra.websocket import Channel, Client
from datetime import datetime 


bestbid = bestask = legitvol = fakevol = num_fake_trades = num_legit_trades = 0
bidsd = {}
asksd = {}
change = 0

from pprint import pprint

class Ticker(Client):

    # def __init__(self, loop, channel):
    #     super(Client, self).__init__(loop, channel) 

    #     pprint(self.__dict__)
    #     exit()


    def on_message(self, message):
        global bestbid, bestask, legitvol, fakevol, asks, bids, asksd, bidsd, change, num_fake_trades, num_legit_trades
        global va 

        if message['type'] == 'snapshot':
            #print(message)
            bids=message['bids']
            for el in bids:
                bidsd[ float(el[0]) ] = el[1]
            k=sorted(bidsd.keys(), reverse = True)
            va.bestbid = k[0]
            asks=message['asks']
            for l3 in asks:
                asksd[ float(l3[0]) ] = l3[1]
            l=sorted(asksd.keys())
            va.bestoffer=l[0]     
            print("Best bid: $" + str(va.bestbid) + ", Best offer: $" + str(va.bestoffer))

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
                va.bestbid = k[0]
                #print(bidsd.get(price))
                #for k in sorted (bidsd, reverse=True):
                #   print((k, bidsd[k]), end = " ")
            if message['changes'][0][0] == 'sell':
                if qty!=0.0:
                    asksd.update({price:qty})
                else:
                    asksd.pop(price)
                l=sorted(asksd.keys())
                va.bestoffer=l[0]
            if va.bestoffer <= va.bestbid:
                print("########################## BOOK CROSS ################")
            else:

                # Eg 2020-04-20T09:17:03.179195Z
                ts = datetime.strptime(timestamp, "%Y-%m-%dT%H:%M:%S.%fZ")
                ts_milis = (ts - datetime.utcfromtimestamp(0)).total_seconds() * 1000 
                data = {
                    'u' : float(ts_milis), # Unique, order book updateId
                    'bb': float(va.bestbid),  # best bid 
                    'bo': float(va.bestoffer), # best offer
                    'bq': float(0), # best bid qty
                    'aq': float(0), # best ask qty
                }
                va.process_book_entry(data)


        elif message['type'] == 'match':

            # pprint(message)
            # exit()

            ts = datetime.strptime(message['time'], "%Y-%m-%dT%H:%M:%S.%fZ")
            ts_milis = (ts - datetime.utcfromtimestamp(0)).total_seconds() * 1000 
            data = { 
                'ts': ts_milis,
                'price': float(message['price']),
                'qty': float(message['size']),
            }
            va.process_trade_entry(data) 
            va.print_summary()



if __name__ == "__main__":

    va = VolumeAnalyser('Coinbase')
    va.set_symbol_info( { 'symbol': 'BTCUSD', 'base_asset': 'BTC', 'quote_asset': 'USD'} ) 

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

