## Binance Fake Volume Checker

```
pip install -r requirements.txt
python binance_fake_volume_checker.py
```

### Explanation of the script 
The script subscribes to the websocket feed for the 2 most real time data sources available.
- The individual book ticker - [binance api link](https://github.com/binance-exchange/binance-official-api-docs/blob/master/web-socket-streams.md#individual-symbol-book-ticker-streams)
- The real time trade execution feed - [binance api link](https://github.com/binance-exchange/binance-official-api-docs/blob/master/web-socket-streams.md#trade-streams)
The script utilize the `python-binance` library found [here](https://github.com/sammchardy/python-binance)  

The idea is simple, stream the most real time feeds of the order book best bid/offer and the trades and look for trades which happen inbetween the best bid/offer. These are flagged as 'fake volume' trades since they effectively took from the book a trade which was never on the book, thus executed between the spread. 

Preview of terminal output:
![preview](https://i.imgur.com/0liF9wA.png)  

--- 

#### An anonymous indepdentend code reviewer wrote: 
> - theory: central limit orderbooks have trade executions which require that one side is a maker, and one side is a taker. this means that for every execution there must also be a corresponding book update at that price reflecting a maker order. any trade events reported which violate this price-time priority law of central limit orderbooks indicates fake volume activity reported by the exchange.

> - to test the above theory, real-time websocket stream data from binance is utilised to check that everything is line.

> - the code subscribes to BTCUSDT orderbook feed which is realtime and produces best bid and offer prices and quantities along with orderbook update uid monotonically increasing 

> - the code subscribes to BTCUSDT trade feed which is realtime and produces execution price and quantity along with timestamps for event and trade

> - the code correctly checks orderbook data first, followed by trade data to check whether trade events occur at a price which does not match the most recent orderbook event's best bid/offer

> - i checked verbose outputs of both streams and verified that the timestamps occur chronologically and the orderbook updates are also chronological

> - one potential issue is that the orderbook updates only contain monotonically increasing integer uid rather than an event timestamp or a book update timestamp. this is not ideal as we would prefer to be able to compare the timestamps from bitstamps system across both streams

> - barring any issue with the lack of timestamp on book data it appears there are a number of trade events reported with executins that occur at prices that are greater than the last book update's best offer and less than the best ask, which would not be possible.