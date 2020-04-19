from binance.client import Client
client = Client("DdEn5fpqEAekNJCVYmflOY9pLfIozLTjU4qXm5HqB9vyFh9PAB7LNdBWPjrkHf43", "c5NjpuJPGYgQZ60ZUXE3z6FQTV3YVOTNVz5JZ5aW2ST3uTJM65mykaFjCDMhPa1D")

from binance.websockets import BinanceSocketManager
import time
from pprint import pprint
import os
import zmq
import json  


def mogrify(topic, msg):
    """ json encode the message and prepend the topic """
    return topic + ' ' + json.dumps(msg,  default=str)


class BinanceChecker: 

    def __init__(self):

        self.context = zmq.Context()
        self.consumer_sender = self.context.socket(zmq.PUB)
        self.consumer_sender.connect('tcp://127.0.0.1:5000')

        self.last_bid = 0
        self.last_ask = 0 
        self.faked_volume = 0
        self.legit_volume = 0
        self.last_trade_time = 0 
        self.num_fake_trades = 0
        self.num_legit_trades = 0

    def send_to_zmq(self, data):
        data = mogrify('binance_output', data)
        self.consumer_sender.send_string(data, zmq.NOBLOCK)


    def run(self):

        def process_message(msg):
            # os.system('clear')
            # global last_bid, last_ask, faked_volume, legit_volume, last_trade_time, num_fake_trades, num_legit_trades

            # pprint(last_trade_time)
            # os._exit(1)

            # Is a order book stream update
            # Since the 'A' key is only present in the book ticker stream
            if 'A' in msg:
                self.last_bid = msg['b']
                self.last_ask = msg['a']
                self.send_to_zmq( {'action': 'book_update', 'last_bid':self.last_bid, 'last_ask': self.last_ask} )
                print('\u001b[38;5;83m', self.last_bid, '\033[0m', '\u001b[38;5;244m', '----', '\033[0m', '\u001b[38;5;196m', self.last_ask, '\033[0m')

            # Is a trade stream update 
            else:
                trade_time = msg['T'] 

                # Check this trade time is AFTEr the last trade time
                # This ensures the trades we're seeing are indeed in order
                # and not some lagged trade coming through from some post settlment process etc on binances end
                # This is in miliseconds which does not actually have enough precision 
                if trade_time < self.last_trade_time:
                    self.send_to_zmq({'action': 'error', 'msg': 'ERROR, Trade Time does not follow chronological order'})
                    print('\033[96m', 'ERROR, Trade Time does not follow chronological order', '\033[0m')

                # Check if the trade occured above the last best bid, and below the last best ask
                # Thus occured 'between the spread' 
                if ( ( msg['p'] > self.last_bid ) and (msg['p'] < self.last_ask) ):
                    self.send_to_zmq({'action': 'order_mismatch', 'msg': '-- EXECUTION BETWEEN SPREAD (_o_): '+str(msg['T'])+'--'+str(msg['p'])+' for '+str(msg['q'])})
                    print('\033[93m', '-- EXECUTION BETWEEN SPREAD (_o_): ', msg['T'], '--', msg['p'], 'for', msg['q'], '\033[0m')

                    self.faked_volume = self.faked_volume + float(msg['q'])
                    self.num_fake_trades = self.num_fake_trades + 1
                else:
                    self.send_to_zmq({'action': 'order_legit', 'msg': '-- Legit Trade: '+str(msg['T'])+'--'+str(msg['p'])+' for '+str(msg['q'])})
                    print('\u001b[38;5;244m', '-- Legit Trade: ', msg['T'], '--', msg['p'], 'for', msg['q'], '\033[0m')

                    self.legit_volume = self.legit_volume + float(msg['q'])
                    self.num_legit_trades = self.num_legit_trades + 1


                self.send_to_zmq({'action': 'summary', 
                    'total_trades': (self.num_fake_trades+self.num_legit_trades),
                    'sum_fake_volume': self.faked_volume,
                    'sum_legit_volume': self.legit_volume,
                    'sum_fake_trades': self.num_fake_trades,
                    'sum_legit_trades': self.num_legit_trades,
                })
                print('\033[95m', 'total fake volume: ', self.faked_volume, ' BTC', '\033[0m')
                print('\033[95m', 'total legit volume: ', self.legit_volume, ' BTC', '\033[0m')
                print('\033[95m', 'number of fake trades: ', self.num_fake_trades, '\033[0m')
                print('\033[95m', 'number of legit trades: ', self.num_legit_trades, '\033[0m')



        bm = BinanceSocketManager(client)

        # Real time book ticker stream
        # https://github.com/binance-exchange/binance-official-api-docs/blob/master/web-socket-streams.md#individual-symbol-book-ticker-streams
        # https://github.com/sammchardy/python-binance/blob/c66695a785e8d3cf0975d09b624f79772dac4115/binance/websockets.py#L409
        bm.start_symbol_book_ticker_socket('BTCUSDT', process_message)

        # Real time trade execution feed
        # https://github.com/binance-exchange/binance-official-api-docs/blob/master/web-socket-streams.md#trade-streams
        # https://github.com/sammchardy/python-binance/blob/c66695a785e8d3cf0975d09b624f79772dac4115/binance/websockets.py#L254
        bm.start_trade_socket('BTCUSDT', process_message)
        bm.start()



if __name__ == "__main__":
    App = BinanceChecker()
    App.run()