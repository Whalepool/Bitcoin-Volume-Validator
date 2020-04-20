
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

class VolumeAnalyser():

    def __init__(self, exchange, output_print):

        self.context = zmq.Context()
        self.consumer_sender = self.context.socket(zmq.PUB)
        self.consumer_sender.connect('tcp://127.0.0.1:5000')

        self.exchange = exchange
        self.output_print = output_print
        self.started = datetime.utcnow()
        self.bestbid = 0
        self.bestoffer = 0 
        self.faked_volume = 0
        self.legit_volume = 0
        self.last_trade_time = 0 
        self.num_fake_trades = 0
        self.num_legit_trades = 0


    def send_to_zmq(self, action, input_data):
        output_data = { 
            'action': action, 
            'data': input_data,
            'summary': {
                'exchange_name': self.exchange,
                'started': self.started.strftime("%Y-%m-%d %H:%M"),
                'running_duration': (datetime.utcnow()-self.started).seconds,
                'total_trades': (self.num_fake_trades+self.num_legit_trades),
                'sum_fake_volume': self.faked_volume,
                'sum_legit_volume': self.legit_volume,
                'sum_fake_trades': self.num_fake_trades,
                'sum_legit_trades': self.num_legit_trades,
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
            out  = '\u001b[38;5;248m ' +'{:<18}'.format(str(data['u'])) +' \033[0m'
            if data['bq'] > 0:
                out += '\u001b[38;5;70m '  +'{:8.6}'.format(data['bq'])     +' \033[0m'
            out += '\u001b[38;5;83m '  +'{:^10.8}'.format(data['bb'])   +' \033[0m'
            out += '\u001b[38;5;244m ' +'----'                          +' \033[0m'
            out += '\u001b[38;5;196m ' +'{:^10.8}'.format(data['bo'])   +' \033[0m'
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
                print('\033[93m', '-- EXECUTION BETWEEN SPREAD (_o_): ', data['ts'], '--', data['price'], 'for', data['qty'], '\033[0m')

            self.faked_volume = self.faked_volume + data['qty']
            self.num_fake_trades = self.num_fake_trades + 1

        else:
            self.send_to_zmq('order_legit', data)
            if self.output_print == True:
                print('\u001b[38;5;244m', '-- Legit Trade: ', data['ts'], '--', data['price'], 'for', data['qty'], '\033[0m')

            self.legit_volume = self.legit_volume + data['qty']
            self.num_legit_trades = self.num_legit_trades + 1


    def print_summary(self):
        if self.output_print == True:
            print('\033[95m', 'total fake volume: ', self.faked_volume, ' BTC', '\033[0m')
            print('\033[95m', 'total legit volume: ', self.legit_volume, ' BTC', '\033[0m')
            print('\033[95m', 'number of fake trades: ', self.num_fake_trades, '\033[0m')
            print('\033[95m', 'number of legit trades: ', self.num_legit_trades, '\033[0m')