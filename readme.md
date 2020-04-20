## Crypto Exchange Volume Validator

```
pip install -r requirements.txt  
python binance_check.py  
python kraken_check.py  
python coinbase_check.py  
python ftx_check.py  
python bitstamp_check.py  
```
  
### Theory  

Every trade execution by law of Central Limit Order Book logic has both a "maker" and a "taker" side from orders created.

Every "maker" order has an event pushed to the "OrderBook" websocket stream.

The API documentation in all cases of exchanges used indicates real-time pushing of updated data (we did not use streams where there was indication of 1000ms or so delays).

So the methodology used throughout is to programmatically watch:  
 - The order book best bid/offer   
 - The raw trade feed     

Then look for trades which occur inbetween the bid/ask.

This would indicate a trade took place which no one else was able to execute because the trade never appeared on the order book for anyone to be able to see, to then take.

It is known that some exchanges are just not good at reporting the orderbook data and trade data in synch, or they do not provide detailed enough information of event timestamp/id to be able to resolve suspicious data.

The scripts here compute both Fake Trades Count vs Legit Trades Count, as well as Fake Volume vs. Legit Volume.

Feel free to request an exchange you use to be analysed using our methodology and we'll be happy to post it along with results.

### Suggestion for Exchanges

Our suggestion to exchanges:

- Provide EVENT and MESSAGE timestamps in nanoseconds for book and trade data

- Provide monotonically increasing integer EVENT id's in both book and trade data

If this data is provided then some, if not all, of the discrepancies can be explained.
    
| Exchange        | Volume executed between the spread (\_o\_) ? | Notes  |  
| ------------- |:-------------:|:----- |  
| Binance | **30%** | Approx 30% of volume executes between the spread |   
| Coinbase     | **2-3%** | Approx 2-3% of volume executes between the spread |  
| Bitstamp | **<1%**      | Tested over a 12h period  | 
| FTX     | **<1%** | within margin of error for latency issues |  
| Kraken | **0%**      |  **PERFECT** - Tested and no fake volume identified  |   
| Bitfinex     | -      |   Exchange has hidden orders so test is non applicable |  
| "Bilaxy"  | **YES** |  Totally fake. See [video](https://www.youtube.com/watch?v=eHZ_p0pRYi4) | 

---   
    
#### Binance  Notes
Results for BTCUSDT approx 20-40% fake orders

The script subscribes to the websocket feed for the 2 most real time data sources available.
- The individual book ticker - [binance api link](https://github.com/binance-exchange/binance-official-api-docs/blob/master/web-socket-streams.md#individual-symbol-book-ticker-streams)
- The real time trade execution feed - [binance api link](https://github.com/binance-exchange/binance-official-api-docs/blob/master/web-socket-streams.md#trade-streams)
The script utilize the `python-binance` library found [here](https://github.com/sammchardy/python-binance)  

The idea is simple, stream the most real time feeds of the order book best bid/offer and the trades and look for trades which happen inbetween the best bid/offer. These are flagged as 'fake volume' trades since they effectively took from the book a trade which was never on the book, thus executed between the spread. 


###### Binance  Critism   
  
It is possible the trades coming through on this raw feed come through post binance internal settlement.  
They maybe using some distributed nodes to process this trade execution queue.   
Some of those processes maybe incur some micro lag vs others thus get pushed to the ws stream may not be 100% chronological.  
I have tried to use the 'trade time' to check for this but unfortunately this is only in miliseconds and so does not offer the level of precision to truely determine if the trades coming through the raw trades feed are indeed chronological.

We recommend that Binance and other exchanges include both highly-precise timestamp data for events (not just sending message) as well as integer uid to establish order of events to establish the unambiguous system order.


Preview of binance output:    
  
![preview](https://i.imgur.com/1gLUDzc.png)  
  
Given that binances volume is so out of step with other trusted western exchanges, to the order of 5-10x more, it's not surprising that the scripts show such a high percentage of volume which seems very 'questionable' to say the least.  
  
Exhibit a:  
  
![Binance Volume out of sync with other trusted exchanges](https://i.imgur.com/94komRR.jpg)  
    
  
#### An anonymous independent code reviewer wrote with regards to binance.py: 
> - theory: central limit orderbooks have trade executions which require that one side is a maker, and one side is a taker. this means that for every execution there must also be a corresponding book update at that price reflecting a maker order. any trade events reported which violate this price-time priority law of central limit orderbooks indicates fake volume activity reported by the exchange.

> - to test the above theory, real-time websocket stream data from binance is utilised to check that everything is line.

> - the code subscribes to BTCUSDT orderbook feed which is realtime and produces best bid and offer prices and quantities along with orderbook update uid monotonically increasing 

> - the code subscribes to BTCUSDT trade feed which is realtime and produces execution price and quantity along with timestamps for event and trade

> - the code correctly checks orderbook data first, followed by trade data to check whether trade events occur at a price which does not match the most recent orderbook event's best bid/offer

> - i checked verbose outputs of both streams and verified that the timestamps occur chronologically and the orderbook updates are also chronological

> - one potential issue is that the orderbook updates only contain monotonically increasing integer uid rather than an event timestamp or a book update timestamp. this is not ideal as we would prefer to be able to compare the timestamps across both streams

> - barring any issue with the lack of timestamp on book data it appears there are a number of trade events reported with executions that occur at prices that are greater than the last book update's best offer and less than the best ask, which would not be possible.    
  
--- 

#### Coinbase  Notes
The coinbase test is built using the `copra` python library [https://github.com/tpodlaski/copra](https://github.com/tpodlaski/copra).  
The idea of latency to explain these readings can be ruled out in that all trades that came through never crossed the book. Book crossing would be a clear sign of some latency mis matching yet this never happened.
 
However, the streams on Coinbase were incredibly fast and in many cases events pushed on the same exact nanosecond timestamp. Because of this, we would have liked some integer uid that established the order of events in such cases so it could be disentangled, but this is currently not possible. 
 
Preview of Coinbase output:        
      
![preview](https://i.imgur.com/O79uQTJ.png)  

---   
  
#### Bitstamp  Notes  
Subscribing to `order_book_btcusd` and `live_trades_btcusd` watching over a period of time produced 0 fake orders. 

Preview of Coinbase output:        
      
![preview](https://i.imgur.com/8dUeGn7.png) 
  
--- 

#### FTX  Notes
The FTX test was done subscribing to bitcoin perps trades and order book.
Trade anomalies executing between the spread totalled approx <1% of volume which could be put down to the margin of error for latency related issues.
   
Preview of FTX output:        
      
![preview](https://i.imgur.com/ph60g9G.png)   

---   
  
#### Kraken  Notes  

Kraken was the only exchange where we consistently got absolutely 0 fake trades printed. Kraken provides data on both the book and trade stream using precise timestamps and the order and the CLOB logic was always respected in our analysis.
   
Preview of Kraken output:        
      
![preview](https://i.imgur.com/wTgnHVG.png)  
  
---  

#### Bitfinex  Notes
Bitfinex has hidden orders so orders which might execute between the best bid/offer could easily be written off as a hidden order
  
---   
    
#### Bilaxy  Notes
This exchange, among others, is regularly cited was one of the top exchanges on many websites.  

Image:    
[image of fake exchanges](https://i.imgur.com/k41FM3X.png)   
 
This exchange amongst others are included by coinmarketcap.com and coincap.io and such in their listings and volume reporting, leading to very skewed data.  

Below is a video from the Bilaxy website showing trades just executing between the spread   

[![Bilaxy](https://i.imgur.com/hSdw9XJ.png)](https://www.youtube.com/watch?v=eHZ_p0pRYi4)    
  
---  
 
