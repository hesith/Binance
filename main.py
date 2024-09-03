from trade_client import *
from store_order import *
from load_config import *

from datetime import datetime, time
import time

import json
import os.path


# loads local configuration
config = load_config('config.yml')


class timeframe:
    ONE_MIN = '1m'
    THREE_MIN = '3m'
    FIVE_MIN = '5m'
    TEN_MIN = '10m'
    FIFTEEN_MIN = '15m'
    THIRTY_MIN = '30m'
    FORTY_FIVE_MIN = '45m'
    ONE_HOUR = '1h'
    TWO_HOUR = '2h'
    THREE_HOUR = '3h'
    FOUR_HOUR = '4h'

class bcolors:
    HEADER = '\033[95m'
    OKBLUE = '\033[94m'
    OKCYAN = '\033[96m'
    OKGREEN = '\033[92m'
    WARNING = '\033[93m'
    FAIL = '\033[91m'
    ENDC = '\033[0m'
    BOLD = '\033[1m'
    UNDERLINE = '\033[4m'



#Variables
targetSymbol = 'HARD'+'USDT'
targetTimeframe = timeframe.ONE_MIN
targetInvestment = 10

#Fields
candles = []
candleQueue = []

isBought = False
boughtQty = '0.0'
slTp = '9999999.0'

def get_all_coins():
    """
    Returns all coins from Binance
    """
    return client.get_all_tickers()


def get_new_coins(all_coins):
    """
    Returns new coins and the new coin list
    """
    all_coins_recheck = get_all_coins()
    return [new_coins for new_coins in all_coins_recheck if new_coins['symbol'] not in [coin['symbol'] for coin in all_coins]], all_coins_recheck




def get_price(coin, pairing):
    """
    Get the latest price for a coin
    """
    return client.get_ticker(symbol=coin+pairing)['lastPrice']




# def main():
#     """
#     Sells, adjusts TP and SL according to trailing values
#     and buys new coins
#     """
#     # store config deets
#     tp = config['TRADE_OPTIONS']['TP']
#     sl = config['TRADE_OPTIONS']['SL']
#     enable_tsl = config['TRADE_OPTIONS']['ENABLE_TSL']
#     tsl = config['TRADE_OPTIONS']['TSL']
#     ttp = config['TRADE_OPTIONS']['TTP']
#     pairing = config['TRADE_OPTIONS']['PAIRING']
#     qty = config['TRADE_OPTIONS']['QUANTITY']
#     frequency = config['TRADE_OPTIONS']['RUN_EVERY']
#     test_mode = config['TRADE_OPTIONS']['TEST']

#     all_coins = get_all_coins()

#     while True:

#         # check if the order file exists and load the current orders
#         # basically the sell block and update TP and SL logic
#         if os.path.isfile('order.json'):
#             order = load_order('order.json')

#             for coin in list(order):

#                 # store some necesarry trade info for a sell
#                 stored_price = float(order[coin]['price'])
#                 coin_tp = order[coin]['tp']
#                 coin_sl = order[coin]['sl']
#                 volume = order[coin]['volume']

#                 last_price = get_price(coin, pairing)

#                 # update stop loss and take profit values if threshold is reached
#                 if float(last_price) > stored_price + (stored_price*coin_tp /100) and enable_tsl:
#                     # increase as absolute value for TP
#                     new_tp = float(last_price) + (float(last_price)*ttp /100)
#                     # convert back into % difference from when the coin was bought
#                     new_tp = float( (new_tp - stored_price) / stored_price*100)

#                     # same deal as above, only applied to trailing SL
#                     new_sl = float(last_price) - (float(last_price)*tsl /100)
#                     new_sl = float((new_sl - stored_price) / stored_price*100)

#                     # new values to be added to the json file
#                     order[coin]['tp'] = new_tp
#                     order[coin]['sl'] = new_sl
#                     store_order('order.json', order)

#                     print(f'updated tp: {round(new_tp, 3)} and sl: {round(new_sl, 3)}')

#                 # close trade if tsl is reached or trail option is not enabled
#                 elif float(last_price) < stored_price - (stored_price*sl /100) or float(last_price) > stored_price + (stored_price*tp /100) and not enable_tsl:

#                     try:

#                         # sell for real if test mode is set to false
#                         if not test_mode:
#                             sell = create_order(coin+pairing, coin['volume'], 'SELL')


#                         print(f"sold {coin} at {(float(last_price) - stored_price) / float(stored_price)*100}")

#                         # remove order from json file
#                         order.pop(coin)
#                         store_order('order.json', order)

#                     except Exception as e:
#                         print(e)

#                     # store sold trades data
#                     else:
#                         if os.path.isfile('sold.json'):
#                             sold_coins = load_order('sold.json')

#                         else:
#                             sold_coins = {}

#                         if not test_mode:
#                             sold_coins[coin] = sell
#                             store_order('sold.json', sold_coins)
#                         else:
#                             sold_coins[coin] = {
#                                         'symbol':coin+pairing,
#                                         'price':last_price,
#                                         'volume':volume,
#                                         'time':datetime.timestamp(datetime.now()),
#                                         'profit': float(last_price) - stored_price,
#                                         'relative_profit': round((float(last_price) - stored_price) / stored_price*100, 3)
#                                         }

#                             store_order('sold.json', sold_coins)

#         else:
#             order = {}

#         # store new coins and rechecked coins list here
#         new_coins, all_coins_recheck = get_new_coins(all_coins)

#         # the buy block and logic pass
#         if len(new_coins) > 0:

#             all_coins = all_coins_recheck
#             print(f'New coins detected: {new_coins}')

#             for coin in new_coins:

#                 # buy if the coin hasn't already been bought
#                 if coin['symbol'] not in order:
#                     print(f"Preparing to buy {coin['symbol']}")

#                     price = get_price(coin['symbol'], pairing)
#                     volume = convert_volume(coin['symbol']+pairing, qty, price)

#                     try:
#                         # Run a test trade if true
#                         if config['TRADE_OPTIONS']['TEST']:
#                             order[coin['symbol']] = {
#                                         'symbol':coin['symbol']+config['TRADE_OPTIONS']['PAIRING'],
#                                         'price':price,
#                                         'volume':volume,
#                                         'time':datetime.timestamp(datetime.now()),
#                                         'tp': tp,
#                                         'sl': sl
#                                         }

#                             print('PLACING TEST ORDER')

#                         # place a live order if False
#                         else:
#                             order[coin['symbol']] = create_order(coin['symbol']+config['TRADE_OPTIONS']['PAIRING'], volume, 'BUY')
#                             order[coin['symbol']]['tp'] = tp
#                             order[coin['symbol']]['sl'] = sl

#                     except Exception as e:
#                         print(e)

#                     else:
#                         print(f"Order created with {volume} on {coin['symbol']}")

#                         store_order('order.json', order)
#                 else:
#                     print(f"New coin detected, but {coin['symbol']} is currently in portfolio")

#         else:
#             print(f"No new coins detected, checking again in {frequency} minute(s)..")

#         time.sleep(60*frequency)


# if __name__ == '__main__':
#     main()

def sendBuyOrder():
    return client.create_order(symbol = targetSymbol, side = 'BUY', type = 'MARKET', quoteOrderQty = float(targetInvestment))

def sendSellOrder():
    if(float(boughtQty) > 0):
        return client.create_order(symbol = targetSymbol, side = 'SELL', type = 'MARKET', quantity = float(boughtQty))
    return

def appendCandle(hr, min, lastPrice):
    candleOpenTime = str(hr)+":"+str(min)
    candleOpen = lastPrice
    candles.append({'candleOpenTime':candleOpenTime,'candleOpen':candleOpen})   


def checkLastCandlePerformance():
    isRed = False
    if( len(candles) > 1 ):
        print(str(candles[-1]['candleOpen'])+ " - " +str(candles[-2]['candleOpen']) + " is " + str(float(candles[-2]['candleOpen']) - float(candles[-1]['candleOpen'])))

        if((float(candles[-1]['candleOpen']) - float(candles[-2]['candleOpen'])) > 0):
            isRed = False
        else:
            isRed = True

        if(isRed == True):
            candleQueue.append("R")
        else:
            candleQueue.append("G")

        if(len(candleQueue) > 40):
            candleQueue.pop(0)

        return ("Last candle is "+ (bcolors.OKGREEN+"Green"+bcolors.ENDC)) if(isRed == False) else ("Last candle is "+ (bcolors.FAIL+"Red"+bcolors.ENDC))
    else:
        return "Tracking candles.."


def writeProfits(order, timestamp):
    if(str(order['status']) == 'FILLED' ):
        global isBought 
        global boughtQty 
        global slTp

        if(str(order['side']) == 'BUY'):
            isBought = True
            boughtQty = order['origQty']
            slTp = candles[-2]['candleOpen']
        else:
            isBought = False
            slTp = '9999999.99'

        with open('profitLog.txt', 'a') as the_file:
            the_file.write(str(timestamp) + ' ' + str(order['symbol']) + ' ' + str(order['origQty']) + ' ' + str(order['side']) + ' ' + str(order['cummulativeQuoteQty']) + '\n')

def main():
    global isBought
    global slTp


    while True:
        time.sleep(0.009)
        currentTime = datetime.now()

        if(currentTime.microsecond//10000 == 0):
            print(currentTime)
            hr = currentTime.hour
            min = currentTime.minute
            sec = currentTime.second
            print("Hour: ", hr)
            print("Minute: ", min)
            print("Second: ", sec)

            lastPrice = client.get_ticker(symbol=targetSymbol)['lastPrice']

            print(isBought)
            print(float(lastPrice))
            print(float(slTp))

            if(isBought == True and (float(lastPrice) <= float(slTp)) ):
                writeProfits(sendSellOrder(), currentTime)

            print(lastPrice)

            #print(candles)
            print(candleQueue)

            if(targetTimeframe == timeframe.ONE_MIN):
                if(sec == 0): #MINUTE
                    print("A minute has passed")  

                    appendCandle(hr=hr, min = min, lastPrice = lastPrice)
                    print(checkLastCandlePerformance())       
                    
                    if(isBought == True and candleQueue[-1] == 'R'):
                        writeProfits(sendSellOrder(),currentTime)
                    elif (isBought == True and candleQueue[-1] == 'G'):
                        slTp = candles[-2]['candleOpen']

                    if(len(candleQueue) > 3 and isBought == False):
                        if(candleQueue[-1] == 'G' and candleQueue[-2] == 'R' and candleQueue[-3] == 'R' and candleQueue[-4] == 'R'):
                            writeProfits(sendBuyOrder(), currentTime)

                    

            elif(targetTimeframe == timeframe.FIVE_MIN):
                if(min % 5 == 0 and sec == 0): #5MINUTES
                    print("5 minutes have passed")


        
if __name__ == '__main__':
    main()

