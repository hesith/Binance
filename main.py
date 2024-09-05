from email.mime.text import MIMEText
from multiprocessing.pool import ThreadPool
import smtplib
from threading import Thread
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
    SIX_HOUR = '6h'

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
quoteCurrency = 'USDT'
targetSymbol = 'VITE'+ quoteCurrency
targetTimeframe = timeframe.FIVE_MIN
targetInvestment = 10
trendCheckTimeframe = timeframe.TWO_HOUR

#Fields
candles = []
candleQueue = []
oneMinCandles = []
oneMinCandleQueue = []

coinList = []

isBought = False
boughtQty = '0.0'
slTp = '9999999.0'


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

def appendOneMinCandle(hr, min, lastPrice):
    candleOpenTime = str(hr)+":"+str(min)
    candleOpen = lastPrice
    oneMinCandles.append({'candleOpenTime':candleOpenTime,'candleOpen':candleOpen})  

def checkLastOneMinCandlePerformance():
    isRed = False
    if( len(oneMinCandles) > 1 ):
        print(str(oneMinCandles[-1]['candleOpen'])+ " - " +str(oneMinCandles[-2]['candleOpen']) + " is " + str(float(oneMinCandles[-2]['candleOpen']) - float(oneMinCandles[-1]['candleOpen'])))

        if((float(oneMinCandles[-1]['candleOpen']) - float(oneMinCandles[-2]['candleOpen'])) > 0):
            isRed = False
        else:
            isRed = True

        if(isRed == True):
            oneMinCandleQueue.append("R")
        else:
            oneMinCandleQueue.append("G")

        if(len(oneMinCandleQueue) > 40):
            oneMinCandleQueue.pop(0)

        return ("Last candle (One Minute) is "+ (bcolors.OKGREEN+"Green"+bcolors.ENDC)) if(isRed == False) else ("Last candle is "+ (bcolors.FAIL+"Red"+bcolors.ENDC))
    else:
        return "Tracking one minute candles.."


trendingCoin = ''

def setTrendingCoin():
    coinList.clear()
    global trendingCoin
    for symbol in client.get_all_tickers():
        if(symbol['symbol'].endswith(quoteCurrency)):
            coinList.append(symbol['symbol'])
    
    gainerPercentage = -99999.9999

    for index, relatedSymbol in enumerate(coinList):

        symbol24hrGain = float(client.get_ticker(symbol=relatedSymbol)['priceChangePercent'])
        if(index == 0):
            gainerPercentage = symbol24hrGain
            continue

        if(symbol24hrGain > gainerPercentage ):
            gainerPercentage = symbol24hrGain
            coinList.insert(0, coinList.pop(index))

    trendingCoin = str(coinList[0])
    sendIncomeRepEmail()

txtFilePath = 'profitLog.txt'

def writeProfits(order, timestamp: datetime):
    if(str(order['status']) == 'FILLED' ):
        global isBought 
        global boughtQty 
        global slTp
        global txtFilePath

        txtFilePath = str(timestamp.year) + '_' + str(timestamp.month) + '_' + str(timestamp.day) + '_' + 'income_report' + '.txt'

        if(str(order['side']) == 'BUY'):
            isBought = True
            boughtQty = order['origQty']
            slTp = candles[-2]['candleOpen']
        else:
            isBought = False
            slTp = '9999999.99'

        if(os.path.isfile(txtFilePath)):
            with open(txtFilePath, 'a') as the_file:
                the_file.write(str(timestamp) + ' ' + str(order['symbol']) + ' ' + str(order['origQty']) + ' ' + str(order['side']) + ' ' + str(order['cummulativeQuoteQty']) + '\n')
        else:
             open(txtFilePath, "x")
             with open(txtFilePath, 'a') as the_file:
                the_file.write(str(timestamp) + ' ' + str(order['symbol']) + ' ' + str(order['origQty']) + ' ' + str(order['side']) + ' ' + str(order['cummulativeQuoteQty']) + '\n')

def sendIncomeRepEmail():
    profitOrLoss = 0.0

    with open(txtFilePath, 'r') as fp:
        content = fp.read()
        records = str(MIMEText(content)).splitlines()

        for index,record in enumerate(records):
            if(record.startswith('20')):
                if((record.split(' ')[-2]) == 'SELL' and records[index-1].startswith('20')):
                    profitOrLoss = profitOrLoss + ( float(record.split(' ')[-1]) - float((records[index-1]).split(' ')[-1]))
        content = content + ('\n\n Profit or Loss : '+ str(profitOrLoss))
        msg = MIMEText(content)

    msg['Subject'] = trendCheckTimeframe + ' Income Report'
    msg['From'] = 'hesithsilva@gmail.com'
    msg['To'] = 'hesithgamer@gmail.com'

    s = smtplib.SMTP('smtp.gmail.com',587)
    s.ehlo()
    s.starttls()
    s.login('hesithsilva@gmail.com','zxke dqkw mhng iowk')
    s.sendmail('hesithsilva@gmail.com', ['hesithgamer@gmail.com'], msg.as_string())
    s.quit()

def main():
    global isBought
    global slTp
    global trendingCoin
    global targetSymbol

    while True:
        time.sleep(0.009)
        currentTime = datetime.now()

        if(currentTime.microsecond//10000 == 0):
            print(currentTime)
            hr = currentTime.hour
            min = currentTime.minute
            sec = currentTime.second

            lastPrice = client.get_ticker(symbol=targetSymbol)['lastPrice']

            #print(isBought)
            #print(float(lastPrice))
            #print(float(slTp))

            if(isBought == True and (float(lastPrice) <= float(slTp)) ):
                writeProfits(sendSellOrder(), currentTime)

            print(lastPrice)

            #print(candles)
            print(candleQueue)

            if(sec == 0):
                appendOneMinCandle(hr=hr, min = min, lastPrice = lastPrice)
                checkLastOneMinCandlePerformance()

            if(trendingCoin != ''):
                if(targetSymbol != trendingCoin and isBought == False):
                    candleQueue.clear()
                    candles.clear()
                    oneMinCandleQueue.clear()
                    oneMinCandles.clear()
                    targetSymbol = trendingCoin

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

                    appendCandle(hr=hr, min = min, lastPrice = lastPrice)
                    print(checkLastCandlePerformance())       

                    if(isBought == True and candleQueue[-1] == 'R'):
                        writeProfits(sendSellOrder(),currentTime)
                    elif (isBought == True and candleQueue[-1] == 'G'):
                        writeProfits(sendSellOrder(),currentTime)

                    if(len(candleQueue) > 2 and isBought == False):
                        if(candleQueue[-1] == 'G' and candleQueue[-2] == 'R' and candleQueue[-3] == 'R' and oneMinCandleQueue[-1] != 'R'):
                            writeProfits(sendBuyOrder(), currentTime)
                    
            if(trendCheckTimeframe == timeframe.SIX_HOUR):
                if((hr == 0 or hr % 6 == 0) and min == 0 and sec == 0):
                    
                    pool = ThreadPool(processes=1)
                    pool.apply_async(setTrendingCoin, ()) 
            elif(trendCheckTimeframe == timeframe.TWO_HOUR):
                if((hr == 0 or hr % 2 == 0) and min == 0 and sec == 0):
                    
                    pool = ThreadPool(processes=1)
                    pool.apply_async(setTrendingCoin, ()) 
        
if __name__ == '__main__':
    main()

