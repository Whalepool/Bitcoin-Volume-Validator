## Crypto Exchange Volume Validator

```
pip install -r requirements.txt
python binance.py
python kraken.py
```
  
### Theory  
The idea is to watch 2 things:  
 - The order book best bid/offer   
 - The raw trade feed     

Then look for trades which occur inbetween the bid/ask.       
This would indicate a trade took place which no one else was able to execute because the trade never appeared on the order book for  anyone to be able to see, to then take.     
    
| Exchange        | Volume executed between the spread (\_o\_) ? | Notes  |  
| ------------- |:-------------:|:----- |  
| Binance | **YES** | Approx 30% of volume executes between the spread |   
| Kraken | X      |  Tested and no fake volume identified  |  
| Coinbase     | - | to be confirmed |  
| Bitfinex     | X      |   Exchange has hidden orders so test is non applicable |  
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
I have tried to use the 'trade time' to check for this but unfortunately this is only in miliseconds and so does not offer the level of precision to truely determine if the trades coming through the raw trades feed are indeed chronological  


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

> - one potential issue is that the orderbook updates only contain monotonically increasing integer uid rather than an event timestamp or a book update timestamp. this is not ideal as we would prefer to be able to compare the timestamps from bitstamps system across both streams

> - barring any issue with the lack of timestamp on book data it appears there are a number of trade events reported with executins that occur at prices that are greater than the last book update's best offer and less than the best ask, which would not be possible.

---   
  
#### Kraken  Notes  

Results for XBTEUR 0 fake orders    
   
Preview of binance output:        
      
![preview](https://i.imgur.com/wTgnHVG.png)      
  
--- 

#### Coinbase  Notes
- todo 
  
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
 