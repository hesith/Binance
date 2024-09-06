
import time
#from trade_client import *
#from store_order import *
#from load_config import *

import requests
from bs4 import BeautifulSoup
from selenium import webdriver


# loads local configuration
#config = load_config('config.yml')


URL = "https://www.binance.com/en/support/announcement/new-cryptocurrency-listing?c=48&navId=48&hl=en"



#with open('page.txt', 'w', encoding="utf-8") as the_file:
    #for index,el in enumerate(list):
        #the_file.writelines(str(el)+'\n\n')


def announcement_trigger():
    while (True):
        r = requests.get(URL)
        soup = BeautifulSoup(r.content, 'html5lib') # If this line causes an error, run 'pip install html5lib' or install html5lib
        textContent = soup.get_text()
        list = textContent.split('Binance Futures Will Launch USDⓈ-Margined ')
        
        print(str(list[1].split(' ')[0]))

if __name__ == '__main__':
    announcement_trigger()