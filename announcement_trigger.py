
import os
import time
from trade_client import *
#from store_order import *
from load_config import *

import requests
from bs4 import BeautifulSoup
from selenium import webdriver


# loads local configuration
config = load_config('config.yml')


targetInvestment = 10
target24hrPricePerc = 15

boughtQty = '0.0'
isBought = False
slTp = '9999999.99'

URL = "https://www.binance.com/en/support/announcement/new-cryptocurrency-listing?c=48&navId=48&hl=en"
headers = {'Cache-Control':'no-cache'}

txtFilePath = 'annoucementTriggerLog.txt'

latestFuturesCoin = ''


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


while (True):
    time.sleep(4)

    initialReq = requests.get(URL, headers=headers)
    initialSoup = BeautifulSoup(initialReq.content, 'html5lib') # If this line causes an error, run 'pip install html5lib' or install html5lib
    initialTextContent = initialSoup.get_text()

    initialList = initialTextContent.split('Binance Futures Will Launch USDⓈ-Margined ')  

    if(len(initialList) > 1) : 
        latestFuturesCoin = str(initialList[1].split(' ')[0])
        print('\n\n\n\n\n')
        print("Most recent Binance Futures USDⓈ-Margined listing Announcement is "+ (bcolors.WARNING+str(latestFuturesCoin)+bcolors.ENDC) )
    break


def writeProfits(order):
    if(str(order['status']) == 'FILLED' ):
        global isBought 
        global boughtQty 
        global slTp

        currentTime = datetime.now()

        if(str(order['side']) == 'BUY'):
            isBought = True
            boughtQty = order['origQty']
            slTp = float(client.get_historical_klines(symbol=str(latestFuturesCoin+'USDT'), interval= client.KLINE_INTERVAL_5MINUTE, limit=1)[0][3]) #Get 5 min kline low
        else:
            isBought = False
            slTp = '9999999.99'

        if(os.path.isfile(txtFilePath)):
            with open(txtFilePath, 'a') as the_file:
                the_file.write(str() + ' ' + str(order['symbol']) + ' ' + str(order['origQty']) + ' ' + str(order['side']) + ' ' + str(order['cummulativeQuoteQty']) + '\n')
        else:
             open(txtFilePath, "x")
             with open(txtFilePath, 'a') as the_file:
                the_file.write(str(currentTime) + ' ' + str(order['symbol']) + ' ' + str(order['origQty']) + ' ' + str(order['side']) + ' ' + str(order['cummulativeQuoteQty']) + '\n')





def sendBuyOrder():
    global latestFuturesCoin

    try:
        return client.create_order(symbol = latestFuturesCoin+'USDT', side = 'BUY', type = 'MARKET', quoteOrderQty = float(targetInvestment))
    except:
        return
    
def sendSellOrder():
    if(float(boughtQty) > 0):
        return client.create_order(symbol = latestFuturesCoin+'USDT', side = 'SELL', type = 'MARKET', quantity = float(boughtQty))
    return



def announcement_trigger():
    global latestFuturesCoin
    global isBought
    global slTp

    print('Listening to Binance Announcements...\n\n\n\n\n')

    while (True):
            time.sleep(0.009)

            if(isBought == False):
                r = requests.get(URL, headers=headers)
                soup = BeautifulSoup(r.content, 'html5lib') # If this line causes an error, run 'pip install html5lib' or install html5lib
                textContent = soup.get_text()

                list = textContent.split('Binance Futures Will Launch USDⓈ-Margined ')  

                if(len(list) > 1) : 
                    latestFuturesAnnouncementOnBinance = str(list[1].split(' ')[0])

                    if(latestFuturesCoin != latestFuturesAnnouncementOnBinance):
                        print("A New Listing Announcement has appeared! : "+ (bcolors.FAIL+str(latestFuturesCoin)+bcolors.ENDC) )

                        latestFuturesCoin = latestFuturesAnnouncementOnBinance
                        writeProfits(sendBuyOrder())

            else:
                priceResponse = client.get_ticker(symbol=latestFuturesCoin+'USDT')

                lastPrice = float(priceResponse['lastPrice'])
                priceChangePerc24h = float(priceResponse['priceChangePercent'])
                
                if(float(priceChangePerc24h) >= float(target24hrPricePerc)):
                    writeProfits(sendSellOrder())
           
                if( float(lastPrice) <= float(slTp)):
                    writeProfits(sendSellOrder())

if __name__ == '__main__':
    announcement_trigger()