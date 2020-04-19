
from binance_check import BinanceChecker
import zmq
import json
import argparse
from pprint import pprint

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


from prompt_toolkit.application import Application
from prompt_toolkit.document import Document
from prompt_toolkit.buffer import Buffer
from prompt_toolkit.key_binding import KeyBindings
from prompt_toolkit.layout.containers import HSplit, VSplit, Window, WindowAlign, ScrollOffsets
from prompt_toolkit.layout.controls import BufferControl, FormattedTextControl
from prompt_toolkit.layout.layout import Layout
from prompt_toolkit.layout.dimension import LayoutDimension as D
from prompt_toolkit.styles import Style
from prompt_toolkit.widgets import TextArea
from prompt_toolkit.layout.processors import Processor, Transformation
from prompt_toolkit.formatted_text import to_formatted_text, fragment_list_to_text
from prompt_toolkit.layout.margins import Margin, NumberedMargin, ScrollbarMargin
from prompt_toolkit.formatted_text import HTML, FormattedText
from prompt_toolkit import ANSI




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
    ('vline', 'reverse'),
    ('mbline', "fg:ansiyellow bg:black bold"),
    ('lastbid', "#34eb37"),
    ('spacer', "#bfbfbf bold"),
    ('lastask', "#eb4c34"),
    ('status', "#aaaa00"),
    ('status.position', '#aaaa00'),
    ('status.key', '#87992f'),
])



def get_big_text(): 
    return [ 
        ("class:maintitle", 'Volume Monitor running for '),
        ("class:maintitle.since", ' 4 hours '),
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




def make_exchange_container( exchange ): 
    title = FormattedTextControl([ ("class:status", ' '+exchange+' '), ("class:status.key", " "), ])
    exchange = {} 
    exchange['title'] = title
    # exchange['book_buffer'] = FormattedTextControl()
    exchange['book_buffer'] = Buffer()
    exchange['trades_buffer'] = Buffer()
    exchange['summary'] = FormattedTextControl()
    exchange['summary'].text = get_summary_text()
    exchange['container'] = HSplit(
        [
            # The titlebar.
            Window( height=1, content=exchange['title'], align=WindowAlign.LEFT, left_margins=[ScrollbarMargin()], ),
            # Horizontal separator.
            Window(height=1, char="-", style="class:line"),
            # The 'body', like defined above.
            VSplit([
                Window(height=5, width=45, content=exchange['summary'], align=WindowAlign.LEFT, left_margins=[ScrollbarMargin()], ),
                Window(width=1, char=".", style="class:mbline"),
                Window(BufferControl(buffer=exchange['book_buffer']), height=5),
                # Window(height=6, content=exchange['book_buffer']),
            ]),
            Window(height=1, char="-", style="class:line"),
            Window(BufferControl(buffer=exchange['trades_buffer'])),
        ]
    )
    return exchange

exchanges = {}
for e in args.exchanges:
    exchanges[e] = make_exchange_container( allowed_exchanges[e]['name'] )


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

    # output_text = output_field.text + formatted_in+formatted_out

    #     # Add text to output buffer.
    #     output_field.buffer.document = Document(text=output_text, cursor_position=len(output_text))


    context = zmq.Context()
    consumer_receiver = context.socket(zmq.SUB)
    consumer_receiver.bind('tcp://127.0.0.1:5000')
    for exchange_key,exchange_layout in exchanges.items():
        consumer_receiver.setsockopt_string(zmq.SUBSCRIBE, exchange_key+'_output' )

    while True:
        msg = consumer_receiver.recv()
        topic, trade = demogrify(msg.decode("utf-8"))
        exchange_key = topic.split('_')[0]

        if trade['action'] == 'book_update':
            # exchanges[exchange_key]['book_buffer'].insert_text(str(trade)+'\n')
            text = [ 
                ("class:lastbid", ' '+str(trade['last_bid'])+' '), 
                ("class:spacer", ' ------- '),
                ("class:lastask", ' '+str(trade['last_ask'])+' '),
            ]
            exchanges[exchange_key]['book_buffer'].insert_text( str(trade['last_bid'])+' ------- '+str(trade['last_ask'])+'\n' )
            # exchanges[exchange_key]['book_buffer'].text = exchanges[exchange_key]['book_buffer'].text + text

        if trade['action'] == 'summary':
            exchanges[exchange_key]['summary'].text = get_summary_text(data=trade)

        if (trade['action'] == 'order_mismatch') or (trade['action'] == 'order_legit'):
            exchanges[exchange_key]['trades_buffer'].insert_text(str(trade)+'\n')
        # output_text = output_field.text + str(trade)
        # output_field.buffer.document = Document(text=output_text, cursor_position=len(output_text))
        # exchanges['binance']['title'].text = str(trade)

import threading 
t = threading.Thread(target=getmzq)
t.daemon = True
t.start()


application.run()







