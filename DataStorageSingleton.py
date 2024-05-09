# TODO: Implement https://www.giraycoskun.dev/blog/2023/12/18/sharing-data-in-a-flask-app-accross-gunicorn-workers/ 


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


'''
Created on 7 May 2024

@author: kleme
'''
from Crta import Crta


def initialCheckOfData(self):
    for symbol in DataStorageSingleton.symbols.union(DataStorageSingleton.stocks):
        start = int(dt.datetime(2009, 1, 1).timestamp()* 1000)
        DataStorageSingleton._instance.app.logger.info("Checking freshness of data: " + symbol + " ...")
        if symbol in self.get_dfs().keys():
            start = self.get_last_timestamp(symbol)
            last_dt = datetime.fromtimestamp(start/1000)
            duration = 0
            if symbol in DataStorageSingleton._instance.symbols:
                duration = (datetime.now() - last_dt).total_seconds() / 3600
                if duration > 1:
                    DataStorageSingleton._instance.logger.info(str(duration) + " hours old data for " + symbol) 
                    self.pullNewData(symbol, start, DataStorageSingleton.interval)    
            elif symbol in DataStorageSingleton._instance.stocks:
                duration = datetime.now() - last_dt
                if duration.days > 1:
                    DataStorageSingleton._instance.app.logger.info(str(duration.days) + " days old data for " + symbol) 
                    self.pullNewData(symbol, start, DataStorageSingleton.interval)    
    DataStorageSingleton._instance.app.logger.info("Checking done.")


class DataStorageSingleton:
    _instance = None

    symbols = {'BTCUSDT', 'ETHUSDT', 'SOLUSDT', 'ADAUSDT', 'MKRUSDT', 'JUPUSDT', 'RNDRUSDT', 'DOGEUSDT', 'HNTUSDT', 'BCHUSDT', 'TONUSDT'}
    stocks = {'TSLA', 'MSTR', 'GC=F', 'CLSK'}
    interval = 60
    
    
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
            cls._instance.app = args[0]
            
            
            cls._instance.initialize_data_store()
            
            threadInitialCheck = Thread(target = initialCheckOfData, args = ())
            threadInitialCheck.start()

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
    
    @classmethod            
    def writeCrte(self, symbol):
        crteD = []
        for crtaKey in self._instance.crteD.keys():
            crta = self._instance.crteD[crtaKey]
            if crta.symbol in symbol: 
                crteD.append(crta) 

        crtePath = self.getDataPath(symbol) + os.sep + "crte.data"
        try:
            with open(crtePath,'w') as f:
                strJson = jsonpickle.encode(crteD, indent=2)
                f.write(strJson)
                self._instance.app.logger.info("Wrote crte for symbol: " + symbol)
                 
        except:
            if os.path.isfile(crtePath):        
                os.remove(crtePath)
            self._instance.app.logger.error(traceback.format_exc())
            # or
            self._instance.app.logger.info(sys.exc_info()[2])      
            
    @classmethod
    def update_crteD(self, crta: Crta):
        self._instance.crteD[crta.ime] = crta
        self._instance.app.logger.info("Updated new line for symbol: " + crta.symbol + " " + crta.ime);
    
    @classmethod
    def remove_crteD(self, crta: Crta):
        symbol = crta.symbol
        del self._instance.crteD[crta.ime]
        
        self.writeCrte(symbol)
        
    @classmethod
    def get_crteDforSymbol(self, symbol: str):
        crteD = []
        for crtaKey in self._instance.crteD.keys():
            crta = self._instance.crteD[crtaKey]
            if crta.symbol in symbol: 
                crteD.append(crta)         
        return crteD 
    
    @classmethod
    def initialize_data_store(self):
        jsonpickle.set_encoder_options('json', sort_keys=True, indent=4)
        f = lambda x: dt.datetime.utcfromtimestamp(int(x)/1000)
        for symbol in self.symbols.union(self.stocks):
            dataPath = self.getDataPath(symbol) + os.sep + symbol + '.data'            
            if not symbol in self.get_dfs().keys():
                if os.path.isfile(dataPath):
                    if 'BTCUSDT' in symbol:
                        print(symbol)                
                    df = pd.read_csv(dataPath)
                    
                    #dfs[symbol] = dfs[symbol].drop(['timestamp'], axis=1)
                    #dfs[symbol] = dfs[symbol].rename(columns={"timestamp.1": "timestamp"})
                    #f = lambda x: dt.datetime.utcfromtimestamp(int(x)/1000)
                    #dfs[symbol].index = dfs[symbol].timestamp.apply(f)                
                    
                    df = df.drop(['timestamp'], axis=1)
                    df.rename(columns={"timestamp.1": "timestamp"}, inplace=True)
                    df.index = df.timestamp.apply(f)
                    
                    self.update_dfs(symbol, df)
    
        # load crte
        for symbol in DataStorageSingleton.symbols.union(DataStorageSingleton.stocks):
            crtePath = self.getDataPath(symbol) + os.sep + "crte.data"
            DataStorageSingleton._instance.app.logger.info(crtePath)
            if os.path.isfile(crtePath):
                with open(crtePath, 'r') as f:
                    json_str = f.read()
                    crteD = jsonpickle.decode(json_str)
                    for crta in crteD:
                        if crta.symbol == '':
                            crta.symbol = symbol
                        self.update_crteD(crta)
                        
        self._instance.session = None
        if os.path.isfile("./authcreds.json"):
            with open("./authcreds.json") as j:
                creds = json.load(j)
            
            kljuc = creds['kljuc']
            geslo = creds['geslo']
        
            self._instance.session = HTTP(api_key=kljuc, api_secret=geslo, testnet=False)
            
            if self._instance.session != None:
                result = self._instance.session.get_tickers(category="linear").get('result')['list']
                tickers = [asset['symbol'] for asset in result]
                self._instance.app.logger.info(tickers)
        
    @classmethod
    def get_last_timestamp(self, symbol):
        if not symbol in self.get_dfs().keys():
            return int(dt.datetime(2009, 1, 1).timestamp()* 1000)
            #return int(dt.datetime(2024, 1, 1).timestamp()* 1000)
    
        return int(self.get_dfs().get(symbol).timestamp[-1:].values[0])

    @classmethod
    def pullNewData(self, symbol, start, interval):
        added = False
        
        dataPath = self.getDataPath(symbol) + os.sep + symbol + '.data'
        
        while True:
            DataStorageSingleton._instance.app.logger.info(dt.datetime.now(ZoneInfo('Europe/Ljubljana')).strftime("%d.%m.%Y %H:%M:%S") + \
                ' Collecting data for: ' + symbol + ' from ' + \
                dt.datetime.utcfromtimestamp(start/1000).strftime("%d.%m.%Y %H:%M:%S"))
    
            if symbol in DataStorageSingleton.stocks:
                if start==1230764400000:
                    start = int(dt.datetime(2020, 1, 1).timestamp()* 1000)
                stock = yahooFinance.Ticker(symbol)
                startFrom = dt.datetime.fromtimestamp(start/1000).strftime("%Y-%m-%d")
                endFromDt = dt.datetime.fromtimestamp(start/1000) + timedelta(days=350)
                if endFromDt>dt.datetime.now():
                    endFromDt=dt.datetime.now()
                endFrom = endFromDt.strftime("%Y-%m-%d")
                response = stock.history(start=startFrom, end=endFrom, interval='1d')
                latest = self.format_data(response)
                
                latest = latest.rename_axis("timestamp")
                latest.index = latest.index.tz_convert(None)
                latest = latest.sort_index(inplace=False)
                
                latest.index = latest.index.floor('s')
                
                start = latest.iloc[-1]['timestamp']
            else:
                response = self._instance.session.get_kline(category='linear', 
                                             symbol=symbol, 
                                             start=start,
                                             interval=interval).get('result')
                latest = self.format_data(response)
                start = latest.timestamp[-1:].values[0]
            
            self._instance.app.logger.info("received " + str(latest.size) + " records")
            
            if not isinstance(latest, pd.DataFrame):
                break
            
            time.sleep(0.2)
            
            if not symbol in self.get_dfs().keys():
                self.get_dfs()[symbol] = latest
            else:
                self.get_dfs()[symbol] = pd.concat([self.get_dfs()[symbol], latest])
                
            added=True
            self._instance.app.logger.info("Appended data.")
            if len(latest) == 1:
                break
        
        if added:
            
            quotes_list = [
                Quote(d,o,h,l,c,v) 
                for d,o,h,l,c,v 
                in zip(self._instance.dataStorageSingleton.get_dfs()[symbol].index, 
                       self._instance.dataStorageSingleton.get_dfs()[symbol]['open'], 
                       self._instance.dataStorageSingleton.get_dfs()[symbol]['high'], 
                       self._instance.dataStorageSingleton.get_dfs()[symbol]['low'], 
                       self._instance.dataStorageSingleton.get_dfs()[symbol]['close'], 
                       self._instance.dataStorageSingleton.get_dfs()[symbol]['volume'])
            ]
            
            stoRsi = indicators.get_stoch_rsi(quotes_list, 14,14,3,1)        
    
            stoch_rsi = []
            signals = []
            for stochRSIResult in stoRsi:
                stoch_rsi.append(stochRSIResult.stoch_rsi)
                signals.append(stochRSIResult.signal)
    
    
            self._instance.get_dfs()[symbol]['stoRsi'] = stoch_rsi
            self._instance.get_dfs()[symbol]['stoSignal'] = signals
            
            self._instance.get_dfs()[symbol] = self._instance.get_dfs()[symbol].fillna(0) 
    
            self._instance.get_dfs().get(symbol).drop_duplicates(subset=['timestamp'], keep='last', inplace=True)
    
            self._instance.get_dfs().get(symbol).to_csv(dataPath)
            
            self._instance.app.logger.info("Saved to csv.")
            

    @classmethod            
    def format_data(self, response):
        '''
        Parameters
        ----------
        respone : dict
            response from calling get_klines() method from pybit.
    
        Returns
        -------
        dataframe of ohlc data with date as index
    
        '''
        
        data = response.get('list', None)
        if data == None:
            # asume we have stock data
            data = response.rename(columns={
                'Datetime': 'timestamp',
                'Open': 'open',
                'High': 'high',
                'Low': 'low',
                'Close': 'close',
                'Volume': 'volume'
            })
            data['timestamp'] = data.index.to_series()
            data['timestamp'] = pd.to_datetime(data['timestamp']).astype('int64') // 10**6
            #print(data)        
            
        else:
            data = pd.DataFrame(data,
                                columns =[
                                    'timestamp',
                                    'open',
                                    'high',
                                    'low',
                                    'close',
                                    'volume',
                                    'turnover'
                                    ],
                                )
            f = lambda x: dt.datetime.utcfromtimestamp(int(x)/1000)
            data.index = data.timestamp.apply(f)
            #print(data)
        
        if data.empty:
            return 
        
        #return data
    
        return data[::-1].apply(pd.to_numeric)            