# TODO: Implement https://www.giraycoskun.dev/blog/2023/12/18/sharing-data-in-a-flask-app-accross-gunicorn-workers/ 

import claudeTest
import multiprocessing as mp
import pandas as pd
import jsonpickle
import os.path
import pathlib
import traceback
import sys
import datetime as dt
import yfinance as yahooFinance
from datetime import datetime, timezone
from zoneinfo import ZoneInfo
import json
from pybit.unified_trading import HTTP
from pybit.unified_trading import WebSocket
from datetime import timedelta
import time, threading
from stock_indicators import Quote
from stock_indicators import indicators
from threading import Thread
from email.mime.multipart import MIMEMultipart
from email.mime.text import MIMEText
from email.mime.image import MIMEImage
import smtplib
from shapely.geometry import LineString, Point
from shapely import set_precision
from shapely import distance


def gmail(message, symbol):
    global creds
    gmailEmail = creds['gmailEmail']
    gmailPwd = creds['gmailPwd']


    try:
        DataStorageSingleton._instance.app.logger.info('sending email...')
        server = smtplib.SMTP('smtp.gmail.com', 587)
        server.ehlo()
        server.starttls()
        server.login(gmailEmail,gmailPwd)
        #server.set_debuglevel(1)
        
        message["Subject"] = symbol
        message["From"] = gmailEmail
        
        message["To"] = creds['emailTo'] #', '.join(["vid.zivkovic@gmail.com", "klemen.zivkovic@gmail.com"])
        
        server.send_message(message)
        server.close()
        DataStorageSingleton._instance.app.logger.info('sending email...Done.')
    except:
        DataStorageSingleton._instance.app.logger.error("failed to send mail")
        DataStorageSingleton._instance.app.logger.error(traceback.format_exc())


def sendMailForLastCrossSections(symbol, krogci_x, krogci_y):
    i=0;
    text_data='';
    for x in krogci_x:
        text_data = text_data + \
                'time:  ' + x + '\n' + \
                'price: ' + '{:0,.2f}'.format(krogci_y[i]) + ' $USD/BTC\n\n'
        i=i+1;
                      
            
    if text_data!='':
        text = 'https://crypto.zhivko.eu/index.html?pair='+symbol+'\n';
        text = text + 'Crossing happened for ' + symbol + '\n'
        text = text + text_data
        message = MIMEMultipart("alternative")
        part1 = MIMEText(text, "plain")
        message.attach(part1)
        gmail(message, symbol)

'''
Created on 7 May 2024

@author: kleme
'''
from Crta import Crta


def initialCheckOfData():
    for symbol in DataStorageSingleton.symbols.union(DataStorageSingleton.stocks):
        start = int(dt.datetime(2009, 1, 1).timestamp()* 1000)
        DataStorageSingleton._instance.app.logger.info("Checking freshness of data: " + symbol + " ...")
        if symbol in DataStorageSingleton._instance.get_dfs().keys():
            start = DataStorageSingleton._instance.get_last_timestamp(symbol)
            last_dt = datetime.fromtimestamp(start/1000)
            duration = 0
            if symbol in DataStorageSingleton._instance.symbols:
                duration = (datetime.now() - last_dt).total_seconds() / 3600
                if duration > 1:
                    DataStorageSingleton._instance.app.logger.info(str(duration) + " hours old data for " + symbol) 
                    DataStorageSingleton._instance.pullNewData(symbol, start)    
            elif symbol in DataStorageSingleton._instance.stocks:
                duration = datetime.now() - last_dt
                if duration.days > 1:
                    DataStorageSingleton._instance.app.logger.info(str(duration.days) + " days old data for " + symbol) 
                    DataStorageSingleton._instance.pullNewData(symbol, start)    
    DataStorageSingleton._instance.app.logger.info("Checking done.")


currentHour = dt.datetime.now().hour
def repeatPullNewData():
    global currentHour
    if dt.datetime.now().hour != currentHour:
        currentHour = dt.datetime.now().hour
        DataStorageSingleton._instance.app.logger.info("beep - hour changed: " + str(currentHour))
        try:
            for symbol in DataStorageSingleton._instance.symbols.union(DataStorageSingleton._instance.stocks):
                start = int(dt.datetime(2009, 1, 1).timestamp()* 1000)
                #start = int(dt.datetime(2024, 1, 1).timestamp()* 1000)
                if symbol in DataStorageSingleton._instance.get_dfs().keys():
                    DataStorageSingleton._instance.claudRecomendation[symbol] = claudeTest.getSuggestion(DataStorageSingleton._instance.get_dfs()[symbol])
                    start = DataStorageSingleton._instance.get_last_timestamp(symbol)
                else:
                    DataStorageSingleton._instance.claudRecomendation[symbol] = ""
    
                DataStorageSingleton._instance.pullNewData(symbol, start)
                
                krogci_x, krogci_y, krogci_radius = DataStorageSingleton._instance.calculateCrossSections(symbol)
                sendMailForLastCrossSections(symbol, krogci_x, krogci_y)
        except:
            DataStorageSingleton._instance.app.logger.error('Something went wrong retrieving data')
            DataStorageSingleton._instance.app.logger.error(traceback.format_exc())

            
# function to create threads
def threaded_function():
    repeatPullNewData()
 
 
thread = Thread(target = threaded_function, args = ())
thread.start()
thread.join()    


class DataStorageSingleton:
    _instance = None

    symbols = {'BTCUSDT', 'ETHUSDT', 'SOLUSDT', 'ADAUSDT', 'MKRUSDT', 'JUPUSDT', 'RNDRUSDT', 'DOGEUSDT', 'HNTUSDT', 'BCHUSDT', 'TONUSDT'}
    stocks = {'TSLA', 'MSTR', 'GC=F', 'CLSK'}
    
    '''
    manager: mp.Manager()
    dfs: manager.dict
    crteD: manager.dict
    '''  

    def __new__(cls, *args, **kwargs):
        if not cls._instance:
            cls._instance = super().__new__(cls)
            cls._instance.manager = mp.Manager()
            cls._instance.dfs = cls._instance.manager.dict() 
            cls._instance.crteD = cls._instance.manager.dict()
            cls._instance.claudRecomendation = cls._instance.manager.dict()
            cls._instance.app = args[0]
            
            
            cls._instance.initialize_data_store()
            
            threadInitialCheck = Thread(target = initialCheckOfData, args = ())
            threadInitialCheck.start()

            threading.Timer(20, repeatPullNewData).start()
            
        return cls._instance

    @classmethod
    def get_dfs(self):
        return self._instance.dfs

    @classmethod
    def update_dfs(self, symbol: str, df: pd.DataFrame):
        self._instance.dfs[symbol] = df

    @classmethod
    def get_crteD(self):
        return self._instance.crteD


        
    @classmethod
    def getDataPath(self, symbol):
        path = pathlib.Path("." + os.sep + symbol).resolve()
        if not (os.path.isdir(path)):
            os.mkdir(path, mode = 0o777)
            self._instance.app.logger.info("Directory '% s' created" % path)
        return os.path.realpath(path);        
    
