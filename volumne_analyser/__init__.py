
"""
Bitcoin Volume Analyser
==============
Looking at tick data from various exchanges
"""

# Don't forget to update in `docs/conf.py`!
__version__ = "1.0.0"


__all__ = [
    'VolumeAnalyser',
]


import zmq
import json  
from datetime import datetime, timedelta
import threading 
from pprint import pprint 
import asyncio

class VolumeAnalyser():

    def __init__(self, exchange, output_print=True):


        self.context = zmq.Context()
        self.consumer_sender = self.context.socket(zmq.PUB)
        self.consumer_sender.connect('tcp://127.0.0.1:5000')

        self.exchange = exchange
        self.output_print = output_print
        self.started = datetime.utcnow()
        self.bestbid   = float()
        self.bestoffer = float()
        self.faked_volume = float()
        self.legit_volume = float()
        self.last_trade_time = 0 
        self.faked_trades  = int()
        self.legit_trades = int()
        self.faked_trades_percent = float()
        self.legit_trades_percent = float() 
        self.faked_volume_percent  = float()
        self.legit_volume_percent = float() 

        #set_symbol_info
        self.symbol = 'BTCUSD'
        self.base_asset = 'BTC'
        self.quote_asset = 'USD'

    def set_symbol_info(self, data ):
        self.symbol = data['symbol']
        self.base_asset = data['base_asset']
        self.quote_asset = data['quote_asset'] 

    def send_to_zmq(self, action, input_data):
        output_data = { 
            'action': action, 
            'data': input_data,
            'summary': {
                'exchange_name': self.exchange,
                'symbol': self.symbol,
                'base_asset': self.base_asset,
                'quote_asset': self.quote_asset, 
                'started': self.started.strftime("%Y-%m-%d %H:%M"),
                'running_duration': (datetime.utcnow()-self.started).seconds,
                'total_trades': (self.faked_trades+self.legit_trades),
                'sum_faked_volume': self.faked_volume,
                'sum_legit_volume': self.legit_volume,
                'sum_faked_trades': self.faked_trades,
                'sum_legit_trades': self.legit_trades,
                'faked_trades_percent': self.faked_trades_percent,
                'legit_trades_percent': self.legit_trades_percent,
                'faked_volume_percent': self.faked_volume_percent,
                'legit_volume_percent': self.legit_volume_percent,
            }
        }

        output_data = self.mogrify(self.exchange+'_output', output_data)
        self.consumer_sender.send_string(output_data, zmq.NOBLOCK)

    def mogrify(self, topic, msg):
        """ json encode the message and prepend the topic """
        return topic + ' ' + json.dumps(msg,  default=str)

    def process_book_entry(self, data):

        self.bestbid = data['bb'] 
        self.bestoffer = data['bo'] 

        if self.output_print == True:
            out  = '\u001b[38;5;248m ' +'{:<17}'.format(str(data['u'])) +' \033[0m'
            if data['bq'] > 0:
                out += '\u001b[38;5;70m '  +'{:8.6}'.format(data['bq'])     +' \033[0m'
            out += '\u001b[38;5;83m '  +'{:^10.8}'.format(data['bb'])   +'\033[0m'
            out += '\u001b[38;5;244m ' +'----'                          +'\033[0m'
            out += '\u001b[38;5;196m ' +'{:^10.8}'.format(data['bo'])   +'\033[0m'
            if data['aq'] > 0:
                out += '\u001b[38;5;124m ' +'{:>8.6}'.format(data['aq'])    +' \033[0m'
            print(out)

        self.send_to_zmq( 'book_update', data )


    def process_trade_entry(self, data):

        # Check this trade time is AFTEr the last trade time
        # This ensures the trades we're seeing are indeed in order
        # and not some lagged trade coming through from some post settlment process etc on binances end
        # This is in miliseconds which does not actually have enough precision 
        if data['ts'] < self.last_trade_time: 
            data['msg'] = 'ERROR, Trade Time does not follow chronological order'
            self.send_to_zmq( 'error', data )
            if self.output_print == True:
                print('\033[96m', 'ERROR, Trade Time does not follow chronological order', '\033[0m')
        
        # Check if the trade occured above the last best bid, and below the last best ask
        # Thus occured 'between the spread' 
        if ( ( data['price'] > self.bestbid ) and (data['price'] < self.bestoffer) ):
            self.send_to_zmq('order_mismatch', data)
            if self.output_print == True:
                print('\u001b[38;5;226m', '-- EXECUTION BETWEEN SPREAD (_o_): ', data['ts'], '--', data['price'], 'for', data['qty'], '\033[0m')

            self.faked_volume = self.faked_volume + data['qty']
            self.faked_trades = self.faked_trades + 1

        else:
            self.send_to_zmq('order_legit', data)
            if self.output_print == True:
                print('\u001b[38;5;222m', '-- Legit Trade: ', data['ts'], '--', data['price'], 'for', data['qty'], '\033[0m')

            self.legit_volume = self.legit_volume + data['qty']
            self.legit_trades = self.legit_trades + 1

        self.faked_trades_percent = (self.faked_trades / (self.legit_trades+self.faked_trades)) * 100 
        self.legit_trades_percent = (self.legit_trades / (self.legit_trades+self.faked_trades)) * 100 
        self.faked_volume_percent  = (self.faked_volume / (self.legit_volume+self.faked_volume)) * 100 
        self.legit_volume_percent = (self.legit_volume / (self.legit_volume+self.faked_volume)) * 100  

    def print_summary(self):
        if self.output_print == True:
            # print(out)
            out = '\u001b[38;5;135m '+ '{:<20}'.format('Num of fake trades:')+ ' {:>10.8}'.format(str(self.faked_trades))+  ' '+  '({:.2f}'.format(self.faked_trades_percent)+'%) \033[0m \n'
            out += '\u001b[38;5;135m '+ '{:<20}'.format('Num of legit trades:')+ ' {:>10.8}'.format(str(self.legit_trades))+  ' '+  '({:.2f}'.format(self.legit_trades_percent)+'%) \033[0m \n'
            out += '\u001b[38;5;132m '+ '{:<20}'.format('Total fake volume:')+  ' {:>10.8}'.format(str(self.faked_volume))+  ' '+  '{:>5}'.format(self.base_asset)+  ' ('+'{:.2f}'.format(self.faked_volume_percent)+'%) \033[0m \n'
            out += '\u001b[38;5;132m '+ '{:<20}'.format('Total legit volume:')+ ' {:>10.8}'.format(str(self.legit_volume))+  ' '+  '{:>5}'.format(self.base_asset)+  ' ('+'{:.2f}'.format(self.legit_volume_percent)+'%) \033[0m '
            print(out)