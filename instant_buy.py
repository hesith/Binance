
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
targetCoin = 'HMSTR'

isBought = False

txtFilePath = 'instantyBuLog.txt'



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


def writeProfits(order):
    if(str(order['status']) == 'FILLED' ):
        global isBought 

        currentTime = datetime.now()

        if(str(order['side']) == 'BUY'):
            isBought = True
        else:
            isBought = False

        if(os.path.isfile(txtFilePath)):
            with open(txtFilePath, 'a') as the_file:
                the_file.write(str() + ' ' + str(order['symbol']) + ' ' + str(order['origQty']) + ' ' + str(order['side']) + ' ' + str(order['cummulativeQuoteQty']) + '\n')
        else:
             open(txtFilePath, "x")
             with open(txtFilePath, 'a') as the_file:
                the_file.write(str(currentTime) + ' ' + str(order['symbol']) + ' ' + str(order['origQty']) + ' ' + str(order['side']) + ' ' + str(order['cummulativeQuoteQty']) + '\n')





def sendBuyOrder():
    global targetCoin

    try:
        return client.create_order(symbol = targetCoin+'USDT', side = 'BUY', type = 'MARKET', quoteOrderQty = float(targetInvestment))
    except:
        return
    


def instant_buy():
    global isBought

    print('Trying to buy...\n\n\n\n\n')

    while (True):
            time.sleep(0.009)

            if(isBought == False):

                try:
                    writeProfits(sendBuyOrder())
                except:
                    instant_buy()          

if __name__ == '__main__':
    instant_buy()