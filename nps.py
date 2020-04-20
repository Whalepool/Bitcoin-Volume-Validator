
from binance_check import BinanceChecker
import zmq
import json
import argparse
from pprint import pprint
from datetime import timedelta

parser = argparse.ArgumentParser()
parser.add_argument('-e','--exchanges', nargs='+', help='Exchanges', required=True, default=[])
args = parser.parse_args()

allowed_exchanges = {
    'binance': { 'name': 'Binance' },
    'bitstamp': { 'name': 'Bitstamp' },
    'coinbase': { 'name': 'Coinbase' },
    'ftx': { 'name': 'FTX' },
    'kraken': { 'name': 'Kraken' }
}

for e in args.exchanges:
    if e not in allowed_exchanges:
        msg = e+' is an invalid exchange, allowed are: '+str(list(allowed_exchanges.keys()))
        raise SystemExit(msg)


def demogrify(topicmsg):
    """ Inverse of mogrify() """
    json0 = topicmsg.find('[')
    json1 = topicmsg.find('{')

    start = json0
    if (json1 > 0):
        if (json0 > 0):
            if (json1 < json0):
                start = json1
        else:
            start = json1

    topic = topicmsg[0:start].strip()
    msg = json.loads(topicmsg[start:])

    return topic, msg   #


from prompt_toolkit.application import Application, get_app
from prompt_toolkit.document import Document
from prompt_toolkit.buffer import Buffer
from prompt_toolkit.key_binding import KeyBindings
from prompt_toolkit.layout.containers import HSplit, VSplit, Window, WindowAlign, ScrollOffsets
from prompt_toolkit.layout.controls import BufferControl, FormattedTextControl
from prompt_toolkit.layout.layout import Layout
from prompt_toolkit.layout.dimension import LayoutDimension as D
from prompt_toolkit.styles import Style
from prompt_toolkit.widgets import TextArea, Box
from prompt_toolkit.layout.processors import Processor, Transformation
from prompt_toolkit.formatted_text import to_formatted_text, fragment_list_to_text
from prompt_toolkit.layout.margins import Margin, NumberedMargin, ScrollbarMargin
from prompt_toolkit.formatted_text import HTML, FormattedText
from prompt_toolkit import ANSI
from prompt_toolkit import print_formatted_text




class FormatText(Processor):
    def apply_transformation(self, transformation_input):
        fragments = to_formatted_text(ANSI(fragment_list_to_text(transformation_input.fragments)))
        return Transformation(fragments)


class Buffer_(Buffer):
    def set_text(self, data):
        self.text = data



# The key bindings.
kb = KeyBindings()

@kb.add('c-c')
@kb.add('c-q')
def _(event):
    event.app.exit()


style = Style([
    ('output-field', 'bg:#000044 #ffffff'),
    ('maintitle', '#aaaa00'),
    ('maintitle.since', 'reverse'),
    ('exchangetitle', '#aaaa00 bg:black bold'),
    ('exchangetitle.runtime', 'reverse'),
    ('exchangetitle.prefix', '#fcba03 bg:black bold'),
    ('vline', 'reverse'),
    ('mbline', "fg:ansiyellow bg:black bold"),
    ('lastbid', "#34eb37"),
    ('spacer', "#bfbfbf bold"),
    ('lastask', "#eb4c34"),
    ('status', "#aaaa00"),
    ('status.position', '#aaaa00'),
    ('status.key', '#c6e334'),

    ("book.unique", '#666699'),
    ("book.bq", '#00ff00'),
    ("book.bb", '#33cc33'),
    ("book.spacer", '#666699'),
    ("book.bo", '#cc0000'),
    ("book.aq", '#ff0000'),

])



def get_big_text(): 
    return [ 
        ("class:maintitle", 'Volume Monitor Overview'),
        ("class:maintitle.since", ''),
    ]

def get_title_text(data):
    return [ 
        ("class:exchangetitle.prefix", '⭓'),
        ("class:exchangetitle", ' '+data['exchange_name']+' '),
        ("", "  "),
        ("class:status", " run time: "),
        ("class:exchangetitle.runtime", "{:0>8}".format(str(timedelta(seconds=data['running_duration'])))),
        ("", "  "),
        ("class:status", " started @ "),
        ("class:status", data['started']),

    ]

def get_summary_text(data=None): 
    total_trades = 0
    sum_fake_volume = 0
    sum_legit_volume = 0
    sum_fake_trades = 0
    sum_legit_trades = 0
    if data is not None:
        total_trades = data['total_trades']
        sum_fake_volume = data['sum_fake_volume']
        sum_legit_volume = data['sum_legit_volume']
        sum_fake_trades = data['sum_fake_trades']
        sum_legit_trades = data['sum_legit_trades']

    return [ 
        ("class:status", 'Total Trades: '),
        ("class:status.key", " "+str(total_trades)),
        ("class:status", '\n'),
        ("class:status", "No. of Fake trades: "),
        ("class:status.key", " "+str(sum_fake_trades)+" "),
        ("class:status", '\n'),
        ("class:status", "No. of Legit trades: "),
        ("class:status.key", " "+str(sum_legit_trades)+" "),
        ("class:status", '\n'),
        ("class:status", "Fake volume: "),
        ("class:status.key", " "+str(sum_fake_volume)+" BTC"),
        ("class:status", '\n'),
        ("class:status", "Legit volume: "),
        ("class:status.key", " "+str(sum_legit_volume)+" BTC"),
    ]


def get_buffer_book_text(data):
    return [ 
        ("class:book.unique", '{:<14}'.format(str(data['u']))),   
        ("class:book.bq", '{:8.6}'.format(data['bq'])), 
        ("class:book.bb", '{:^10.8}'.format(data['bb'])),   
        ("class:book.spacer", "-----"),
        ("class:book.bo", '{:^10.8}'.format(data['bo'])),
        ("class:book.aq", '{:>8.6}'.format(data['aq'])),  
    ]

def make_exchange_container( e_key ): 
    exchange = {} 
    exchange['name'] = allowed_exchanges[e_key]['name']
    exchange['title'] = FormattedTextControl()
    exchange['title'].text = HTML('awaiting connection')
    exchange['book_buffer'] = FormattedTextControl()
    exchange['trades_buffer'] = Buffer_()
    exchange['summary'] = FormattedTextControl()
    exchange['summary'].text = get_summary_text()

    exchange['container'] = HSplit(
        [   
            Window(BufferControl(Buffer_()), height=0),
            Window( height=1, content=exchange['title'], align=WindowAlign.LEFT, left_margins=[ScrollbarMargin()], ),
            Window(height=1, char="-", style="class:line"),
            VSplit([
                Window(height=5, width=45, content=exchange['summary'], align=WindowAlign.LEFT, left_margins=[ScrollbarMargin()], ),
                Window(width=1, char=".", style="class:mbline"),
                Window( height=1, content=exchange['book_buffer'], align=WindowAlign.CENTER )
            ]),
            Window(height=1, char="-", style="class:line"),
            Window(
                BufferControl(exchange['trades_buffer'], input_processors=[FormatText()], include_default_input_processors=True),
                # right_margins=[ScrollbarMargin(), ScrollbarMargin()],
            ),
        ]
    )
    return exchange

exchanges = {}
for e_key in args.exchanges:
    exchanges[e_key] = make_exchange_container( e_key )


def get_vsplit():
    out = []
    for i,e in enumerate(args.exchanges):
        out.append(exchanges[e]['container'])
        i += 1
        if i == len(args.exchanges):
            continue 
        out.append(Window(width=1, char="|", style="class:vline"))

    return out

root_root = HSplit([
        # Window( height=1, content=get_big_text(), align=WindowAlign.CENTER ),
        Window( height=1, content=FormattedTextControl(get_big_text), align=WindowAlign.CENTER ),
        Window(height=1, char="-", style="class:line"),
        VSplit(get_vsplit())
    ])

# Run application.
application = Application(
    layout=Layout(root_root),
    key_bindings=kb,
    style=style,
    mouse_support=True,
    full_screen=True)

import os
def getmzq():

    global exchanges

    context = zmq.Context()
    consumer_receiver = context.socket(zmq.SUB)
    consumer_receiver.bind('tcp://127.0.0.1:5000')
    for exchange_key,exchange_layout in exchanges.items():
        consumer_receiver.setsockopt_string(zmq.SUBSCRIBE, exchanges[exchange_key]['name']+'_output' )

    while True:
        msg = consumer_receiver.recv()
        topic, trade = demogrify(msg.decode("utf-8"))
        exchange_key = topic.split('_')[0].lower()

        if trade['action'] == 'book_update':
            # text = [ 
            #     ("class:lastbid", ' '+str(trade['last_bid'])+' '), 
            #     ("class:spacer", ' ------- '),
            #     ("class:lastask", ' '+str(trade['last_ask'])+' '),
            # ]
            # exchanges[exchange_key]['book_buffer'].text = FormattedText(text)
            # txt = '\n \u001b[38;5;83m '+str(trade['bb'])+' \033[0m \u001b[38;5;244m ------- \033[0m \u001b[38;5;196m '+str(trade['bo'])+' \033[0m '            
            exchanges[exchange_key]['book_buffer'].text = get_buffer_book_text(trade['data'])

            exchanges[exchange_key]['title'].text = get_title_text(trade['summary'])
            exchanges[exchange_key]['summary'].text = get_summary_text(trade['summary'])
            
        if trade['action'] == 'summary':
            exchanges[exchange_key]['title'].text = get_title_text(
                name=exchanges[exchange_key]['name'],
                started=str(trade['started']),
                running_duration="{:0>8}".format(str(timedelta(seconds=trade['running_duration'])))
            )
            exchanges[exchange_key]['summary'].text = get_summary_text(trade['data'])

        if (trade['action'] == 'order_mismatch'):

            txt = '\n'
            txt += '\033[93m' + ' -- EXECUTION BETWEEN SPREAD (_o_): ' +' \033[0m'
            txt += '\033[93m' + ' '+str(trade['data']['ts'])+' '       +' \033[0m'
            txt += '\033[93m' + ' '+str(trade['data']['price'])+' '    +' \033[0m'
            txt += '\033[93m' + ' '+str(trade['data']['qty'])+' '      +' \033[0m'
            exchanges[exchange_key]['trades_buffer'].insert_text( txt )


        if (trade['action'] == 'order_legit'):

            txt = '\n'
            txt += '\u001b[38;5;244m ' + ' -- Legit Trade: '                    +' \033[0m'
            txt += '\u001b[38;5;244m ' + ' '+str(trade['data']['ts'])+' '       +' \033[0m'
            txt += '\u001b[38;5;244m ' + ' '+str(trade['data']['price'])+' '    +' \033[0m'
            txt += '\u001b[38;5;244m ' + ' '+str(trade['data']['qty'])+' '      +' \033[0m'
            exchanges[exchange_key]['trades_buffer'].insert_text( txt )

import threading 
t = threading.Thread(target=getmzq)
t.daemon = True
t.start()


application.run()






