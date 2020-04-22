from volumne_analyser import VolumeAnalyser

import argparse
from pprint import pprint

from binance.client import Client


if __name__ == "__main__":


    parser = argparse.ArgumentParser()
    parser.add_argument('-t','--ticker', help='Ticker', default='BTCUSDT')
    args = parser.parse_args()

    client = Client("DdEn5fpqEAekNJCVYmflOY9pLfIozLTjU4qXm5HqB9vyFh9PAB7LNdBWPjrkHf43", "c5NjpuJPGYgQZ60ZUXE3z6FQTV3YVOTNVz5JZ5aW2ST3uTJM65mykaFjCDMhPa1D")
    exinfo = client.get_exchange_info()
    symbol_hashes = {} 
    for s in exinfo['symbols']:
        symbol_hashes[s['symbol']] = { 
            'symbol': s['symbol'],
            'base_asset': s['baseAsset'],
            'quote_asset': s['quoteAsset'],
        }

    if args.ticker not in symbol_hashes:
        raise SystemExit(args.ticker+' is an invalid binance ticker')


    book = client.get_order_book(symbol=args.ticker, limit=1000)
    cum = 0 
    pair = ['bids','asks']
    liquidity_range_levels = [0.1,0.2,0.5,1,2,5,10]
    lr = { 
        'bids': {},
        'asks': {},
    } 
    for p in pair:
        for i,el in enumerate(book[p]):
            if i == 0:
                bbbo = float(el[0])
                if p == 'bids': 
                    lr['bids'] = { n:{ 'price': bbbo-(bbbo/100)*n, 'cum':0, 'msg': None } for n in liquidity_range_levels } 
                if p == 'asks':
                    lr['asks'] = { n:{ 'price': bbbo+(bbbo/100)*n, 'cum':0, 'msg': None } for n in liquidity_range_levels } 
            try:
                amount = float(el[1])
                price = float(el[0])
                cum += amount 
                book[p][i].append(cum)

                if p == 'bids':
                    for k,node in lr['bids'].items():
                        if price > node['price']:
                            lr['bids'][k]['cum'] += amount
                if p == 'asks':
                    for k,node in lr['asks'].items():
                        if price < node['price']:
                            lr['asks'][k]['cum'] += amount
            except:
                pprint(el)
                pprint("An exception occurred") 

        lowest_bid = float(book['bids'][-1][0])
        for k,node in lr['bids'].items():
            if lowest_bid > node['price']:
                lr['bids'][k]['msg'] = 'Incomplete, Beyond visible range'


        highest_ask = float(book['asks'][-1][0])
        for k,node in lr['asks'].items():
            if highest_ask < node['price']:
                lr['asks'][k]['msg'] = 'Incomplete, Beyond visible range'

    def print_book_liquidity(lr):
        liquidity_range_levels = [0.1,0.2,0.5,1,2,5,10]
        print('\u001b[38;5;196m ', 'Asks', ' \033[0m ')
        for depth in list(reversed(liquidity_range_levels)):
            out  = '{:>5}'.format(str(depth)+'% ')+' '
            out += '{:>8.7}'.format(str(lr['asks'][depth]['price']))+' '
            out += '{:>10.8}'.format(str(lr['asks'][depth]['cum']))+' '
            if lr['asks'][depth]['msg'] != None: 
                out += '{}'.format(str(lr['asks'][depth]['msg']))+' '
            print('\u001b[38;5;196m ', out, ' \033[0m ')

        print('\u001b[38;5;154m ', 'Bids', ' \033[0m ')
        for depth in liquidity_range_levels: 
            out  = '{:>5}'.format(str(depth)+'% ')+' '
            out += '{:>8.7}'.format(str(lr['bids'][depth]['price']))+' '
            out += '{:>10.8}'.format(str(lr['bids'][depth]['cum']))+' '
            if lr['bids'][depth]['msg'] != None: 
             out += '{}'.format(str(lr['bids'][depth]['msg']))+' '
            print('\u001b[38;5;154m ', out, ' \033[0m ')


    pprint(lr)
    print_book_liquidity(lr)
    

    exit()
    # va = VolumeAnalyser('Binance' )
    # va.set_symbol_info( symbol_hashes[args.ticker] ) 
    # main()
