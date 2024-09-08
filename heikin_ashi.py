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

targetSymbol = ''
isBought = False
targetInvestment = 10 #USDT
boughtQty = '0.0'


def calculateRoundFloorFactors(symbol):

    symbolData = client.get_ticker(symbol=symbol)
    pricesList = [symbolData['lastPrice'],symbolData['openPrice'],symbolData['highPrice']]

    roundFactorList = []

    for index,price in enumerate(pricesList):
        fractionalPart = str(price).split('.')[1] 
        zeroCount = 0
        for digit in reversed(fractionalPart):
            if(digit == '0'):
                zeroCount += 1
            else:
                break
        roundFactorList.append(len(fractionalPart) - zeroCount)
    else:
        if(roundFactorList[0] == roundFactorList[1] == roundFactorList[2]):
            roundFactor = roundFactorList[0]
        elif(roundFactorList[1] == roundFactorList[2]):
            roundFactor = roundFactorList[1]
        elif(roundFactorList[0] == roundFactorList[1]):
            roundFactor = roundFactorList[0]
        else:
            roundFactor = roundFactorList[0]

    floorFactor = pow(10,roundFactor)

    return {'roundFactor':roundFactor , 'floorFactor':floorFactor}

def getMovingAverage(symbol, roundFactor, klineTimeframe, limit : int): # limit = 20 means 20MA
    symbolDataList =  client.get_historical_klines(symbol=str(symbol), interval= klineTimeframe, limit=limit+1)

    calculateRoundFloorFactors(symbol)

    movingAvg = 0
    for index,symbolData in enumerate(symbolDataList):
        if(index < limit):
            movingAvg += float(symbolData[4])

    movingAvg /= limit

    return round(movingAvg,roundFactor)


def getHAcandleQueue(symbol, roundFactor, floorFactor, klineTimeframe, klineLimit : int):

    haCandleQueue = []

    klines = client.get_historical_klines(symbol=str(symbol), interval= klineTimeframe, limit=klineLimit)

    for index,kline in enumerate(klines):

        if(index > 0 and index < (klineLimit-1)):

            prevHAOpenPrice = round(float(klines[index-1][1]),roundFactor)
            prevHAClosePrice = round(float(klines[index-1][4]),roundFactor)


            close = (1/4) * (float(kline[1])+float(kline[2])+float(kline[3])+float(kline[4]))
            open = (1/2) * (prevHAOpenPrice + prevHAClosePrice)
            

            roundedClose = math.floor(close * floorFactor)/(floorFactor * 1.0)
            roundedOpen = math.floor(open * floorFactor)/(floorFactor * 1.0)

            difference = roundedClose - roundedOpen

            if(difference > 0):
                haCandleQueue.append('G')
            elif(difference == 0):
                haCandleQueue.append('R')
            else:
                haCandleQueue.append('R')

    return(haCandleQueue) 



trendingCoins = []
coinList = []

def setTopGainerCoins():
    global coinList
    global trendingCoins

    coinList.clear()
    trendingCoins.clear()

    for symbol in client.get_all_tickers():
        if(symbol['symbol'].endswith('USDT')):
            hr24Gain = float(client.get_ticker(symbol=symbol['symbol'])['priceChangePercent'])
            coinList.append({'symbol':symbol['symbol'], '24hrGain': hr24Gain})
    
    coinList = sorted(coinList, key= lambda k: k['24hrGain'], reverse=True)

    for index,coin in enumerate(coinList):
        trendingCoins.append(coin['symbol'])

        if(index == 4):
            break

    return
    
class heikinAshiCandlePattern:
    RRRG = 'RRRG'

def checkHApattern(HAcandleQueue : list, pattern : heikinAshiCandlePattern):

    if( pattern == heikinAshiCandlePattern.RRRG ):
        if(HAcandleQueue[-4] == 'R' and HAcandleQueue[-3] == 'R' and HAcandleQueue[-2] == 'R' and HAcandleQueue[-1] == 'G'):
            return True
        else:
            return False

def coinEligibilityCheck(): # check for Pattern and MA
    if(len(trendingCoins) > 0):
        print(bcolors.FAIL+'COIN ELIGIBILITY SUMMARY'+bcolors.ENDC + '\n')

        for coin in trendingCoins:
            roundFloor = calculateRoundFloorFactors(coin)
            queue = getHAcandleQueue(symbol=coin, roundFactor=int(roundFloor['roundFactor']), floorFactor=int(roundFloor['floorFactor']), klineTimeframe=client.KLINE_INTERVAL_5MINUTE, klineLimit=20)
            ma = getMovingAverage(symbol=coin, roundFactor=int(roundFloor['roundFactor']), klineTimeframe=client.KLINE_INTERVAL_5MINUTE, limit=20)
            lastPrice = float(client.get_ticker(symbol=coin)['lastPrice'])

            isMovingAvgEligible = True if (lastPrice > ma) else False
            isPatternEligible = checkHApattern(HAcandleQueue=queue, pattern=heikinAshiCandlePattern.RRRG)

            print((bcolors.WARNING+str(coin)+bcolors.ENDC))
            print('Heikin Ashi queue : ' + (' '.join(str(c) for c in queue)))
            print('Moving Average : ' + str(ma))
            print('Last Price : ' + str(lastPrice) + '\n\n')

            if(isPatternEligible and isMovingAvgEligible):
                print((bcolors.WARNING+str(coin)+bcolors.ENDC) + ' is Eligible \n')
                return coin

        return ''
    else:
        print(bcolors.FAIL+'TRENDING COINS ARE NOT CAPTURED. UNABLE TO PERFORM ELIGIBILITY CHECK.'+bcolors.ENDC + '\n\n')
        return ''

def sendBuyOrder():
    return client.create_order(symbol = targetSymbol, side = 'BUY', type = 'MARKET', quoteOrderQty = float(targetInvestment))

def sendSellOrder():
    if(float(boughtQty) > 0):
        return client.create_order(symbol = targetSymbol, side = 'SELL', type = 'MARKET', quantity = float(boughtQty))
    return

def writeProfits(order, timestamp: datetime):
    if(str(order['status']) == 'FILLED' ):
        global isBought 
        global boughtQty 

        logFilePath = str(timestamp.year) + '_' + str(timestamp.month) + '_' + str(timestamp.day) + '_' + 'income_report' + '.txt'

        if(str(order['side']) == 'BUY'):
            isBought = True
            boughtQty = order['origQty']
        else:
            isBought = False

        if(os.path.isfile(logFilePath)):
            with open(logFilePath, 'a') as the_file:
                the_file.write(str(timestamp) + ' ' + str(order['symbol']) + ' ' + str(order['origQty']) + ' ' + str(order['side']) + ' ' + str(order['cummulativeQuoteQty']) + '\n')
        else:
             open(logFilePath, "x")
             with open(logFilePath, 'a') as the_file:
                the_file.write(str(timestamp) + ' ' + str(order['symbol']) + ' ' + str(order['origQty']) + ' ' + str(order['side']) + ' ' + str(order['cummulativeQuoteQty']) + '\n')



def sendIncomeRepEmail():
    profitOrLoss = 0.0
    serverTimestamp = (client.get_server_time()['serverTime']) / 1000.0
    localTime = datetime.fromtimestamp(timestamp=serverTimestamp)

    logFilePath = str(localTime.year) + '_' + str(localTime.month) + '_' + str(localTime.day) + '_' + 'income_report' + '.txt'

    if(os.path.isfile(logFilePath)):
        with open(logFilePath, 'r') as fp:
            content = fp.read()
            records = str(MIMEText(content)).splitlines()

            for index,record in enumerate(records):
                if(record.startswith('20')):
                    if((record.split(' ')[-2]) == 'SELL' and records[index-1].startswith('20')):
                        profitOrLoss = profitOrLoss + ( float(record.split(' ')[-1]) - float((records[index-1]).split(' ')[-1]))
            content = content + ('\n\n Profit or Loss : '+ str(profitOrLoss))
            msg = MIMEText(content)

        msg['Subject'] = ' Income Report until' + str(localTime.hour) + ' : ' + str(localTime.minute)
        msg['From'] = 'hesithsilva@gmail.com'
        msg['To'] = 'hesithgamer@gmail.com'

        s = smtplib.SMTP('smtp.gmail.com',587)
        s.ehlo()
        s.starttls()
        s.login('hesithsilva@gmail.com','zxke dqkw mhng iowk')
        s.sendmail('hesithsilva@gmail.com', ['hesithgamer@gmail.com'], msg.as_string())
        s.quit()


def init():
    global isBought
    global targetSymbol

    pool = ThreadPool(processes=1)
    pool.apply_async(setTopGainerCoins, ()) 

    while True:
        time.sleep(0.5)

        serverTimestamp = (client.get_server_time()['serverTime']) / 1000.0
        localTime = datetime.fromtimestamp(timestamp=serverTimestamp)

        if (localTime.minute % 5 == 0 and localTime.second == 0): #5m iteration
            if(isBought == False):
                targetSymbol = coinEligibilityCheck()

                if(targetSymbol != ''):
                    writeProfits(sendBuyOrder(), localTime)
            else:
                roundFloor = calculateRoundFloorFactors(targetSymbol)
                lastHAcandle = getHAcandleQueue(symbol=targetSymbol, roundFactor=int(roundFloor['roundFactor']), floorFactor=int(roundFloor['floorFactor']), klineTimeframe=client.KLINE_INTERVAL_5MINUTE, klineLimit=2)[-1]
            
                if(lastHAcandle == 'R'):
                    writeProfits(sendSellOrder(), localTime)

        if (localTime.minute == 0 and localTime.second == 0): #1h iteration
            pool = ThreadPool(processes=1)
            pool.apply_async(setTopGainerCoins, ())

        if (localTime.hour % 2 == 0 and localTime.minute == 0 and localTime.second == 0): #2h iteration
            pool = ThreadPool(processes=1)
            pool.apply_async(setTopGainerCoins, ())

if __name__ == '__main__':
    init()


while (True):
    continue





