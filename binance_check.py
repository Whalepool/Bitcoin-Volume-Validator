from volumne_analyser import VolumeAnalyser


from binance.client import Client
from binance.websockets import BinanceSocketManager

class BinanceChecker( VolumeAnalyser ) : 

    def __init__(self, exchange, output_print=True):
        VolumeAnalyser.__init__(self, exchange, output_print)

    def run(self):
        def process_message(msg):
            # Is a order book entry 
            if 'A' in msg:
                data = {
                    'u' : int(msg['u']), # Unique, order book updateId
                    'bb': float(msg['b']),  # best bid 
                    'bo': float(msg['a']), # best offer
                    'bq': float(msg['B']), # best bid qty
                    'aq': float(msg['A']), # best ask qty
                }
                self.process_book_entry(data)

            # Is a trade stream update 
            else:
                data = { 
                    'ts': msg['T'],
                    'price': float(msg['p']),
                    'qty': float(msg['q']),
                }
                self.process_trade_entry(data) 
                self.print_summary()


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

    client = Client("DdEn5fpqEAekNJCVYmflOY9pLfIozLTjU4qXm5HqB9vyFh9PAB7LNdBWPjrkHf43", "c5NjpuJPGYgQZ60ZUXE3z6FQTV3YVOTNVz5JZ5aW2ST3uTJM65mykaFjCDMhPa1D")
    App = BinanceChecker('Binance')
    App.run()