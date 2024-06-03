from datetime import datetime, timezone, timedelta
from email.mime.image import MIMEImage
from email.mime.multipart import MIMEMultipart
from email.mime.text import MIMEText
import json
import locale
import logging
import os.path
import pathlib
import smtplib
import sys
from threading import Thread
import time, threading
import traceback
from zoneinfo import ZoneInfo

import pytz
import requests

import jsonpickle 
from pybit.unified_trading import HTTP
from pybit.unified_trading import WebSocket

from shapely import distance
from shapely import set_precision
from shapely.geometry import LineString, Point
from stock_indicators import Quote
from stock_indicators import indicators

from claudeTest import getSuggestion
import datetime as dt
import pandas as pd
import yfinance as yahooFinance
import numpy as np

import decimal

from Crta import Crta

from Util import read, write, delete

from MyFlask import MyFlask

claudRecomendation = dict()
jsonpickle.set_encoder_options('json', sort_keys=True, indent=4)

pd.set_option('display.max_rows', None)
pd.set_option('display.max_columns', None)

currentHour = None

session = None
if os.path.isfile("./authcreds.json"):
    with open("./authcreds.json") as j:
        creds = json.load(j)
    
    kljuc = creds['kljuc']
    geslo = creds['geslo']

    session = HTTP(api_key=kljuc, api_secret=geslo, testnet=False)
    result = session.get_tickers(category="linear").get('result')['list']
    # if (asset['symbol'].endswith('USDT') or asset['symbol'].endswith('BTC'))]
    tickers = [asset['symbol'] for asset in result]
    logging.info("Tickers:")
    logging.info(tickers)
    tickers_data=""    

symbols = {'BTCUSDT', 'ETHUSDT', 'SOLUSDT', 'ADAUSDT', 'MKRUSDT', 'JUPUSDT', 'RNDRUSDT', 'DOGEUSDT', 'HNTUSDT', 'BCHUSDT', 'TONUSDT', 'SUIUSDT', 'BNBUSDT' }
stocks = {'TSLA', 'MSTR', 'GC=F', 'CLSK', 'NVDA', 'GOOG', 'AMZN'}
#symbols = {'BTCUSDT'}
#stocks = {'TSLA'}


symbolsAndStocks = symbols.union(stocks)
interval = 60
locale.setlocale(locale.LC_ALL, 'sl_SI')

def utc_to_milliseconds(utc_string):
    # Parse the UTC string into a datetime object
    utc_datetime = datetime.strptime(utc_string, "%Y-%m-%dT%H:%M:%S.%fZ")
    
    # Calculate the timestamp in milliseconds
    timestamp_ms = int(utc_datetime.timestamp() * 1000)
    
    return timestamp_ms

def format_data(response):
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
        data = response.rename_axis(['datetime'])
        data.rename(columns={
            'Open': 'open',
            'High': 'high',
            'Low': 'low',
            'Close': 'close',
            'Volume': 'volume'
        }, inplace=True)

        '''
        column_to_move = data.pop("datetime")
        data.insert(0, "timestamp", column_to_move)
        
        data.index = data.index.tz_convert(None)
        data.index = data.index.floor('s')
        '''
        data['timestamp'] = data.index.values.astype(np.int64) // 10 ** 9
        
        data = data.sort_index(ascending=False)

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
        
        data['timestamp'] = data['timestamp'].apply(lambda x: int(x)/1000)
        f = lambda x: dt.datetime.utcfromtimestamp(int(x))
        data.index = data.timestamp.apply(f)
        
        #print(data)
    data.index.names = ['datetime']
    
    if data.empty:
        return 
    
    #return data

    return data[::-1].apply(pd.to_numeric)


def getDataPath(symbol):
    path = pathlib.Path("." + os.sep + symbol).resolve()
    if not (os.path.isdir(path)):
        os.mkdir(path, mode = 0o777)
        MyFlask().app().logger.info("Directory '% s' created" % path)
    return os.path.realpath(path);
    
def get_last_timestamp(symbol, dfs):
    ret = 0
    if not symbol in dfs.keys():
        ret = dt.datetime(2020, 1, 1).timestamp()
        #return int(dt.datetime(2024, 1, 1).timestamp()* 1000)
    else:
        ret = dfs.get(symbol).timestamp[-1:].values[0]
    
    dt_float = np.float64(ret)
    seconds_since_epoch = dt_float.astype(np.int64)
    return seconds_since_epoch
    

def pullNewData(symbol, start, dfs):
    global interval
    added = False
    
    dataPath = getDataPath(symbol) + os.sep + symbol + '.data'
    
    if symbol in 'GC=F':
        print('GC=F')
    
    
    while True:
        MyFlask.app().logger.info("start= " + str(start))
        dtObject = datetime.fromtimestamp(start)
        MyFlask.app().logger.info("Start: " + str(dtObject));    
        MyFlask.app().logger.info(dt.datetime.now(ZoneInfo('Europe/Ljubljana')).strftime("%d.%m.%Y %H:%M:%S") + \
            ' Collecting data for: ' + symbol + ' from ' + \
            dt.datetime.fromtimestamp(start).strftime("%d.%m.%Y %H:%M:%S"))
        

        if symbol in stocks:
            if start==1230764400:
                start = int(dt.datetime(2020, 1, 1).timestamp())
            stock = yahooFinance.Ticker(symbol)
            startFrom = dt.datetime.fromtimestamp(start).strftime("%Y-%m-%d")
            endFromDt = dt.datetime.fromtimestamp(start) + timedelta(days=350)
            if endFromDt>dt.datetime.now():
                endFromDt=dt.datetime.now()
            endFrom = endFromDt.strftime("%Y-%m-%d")
            response = stock.history(start=startFrom, end=endFrom, interval='1d')
            
            if len(response) ==0:
                break
            
            latest = format_data(response)
            
            #latest.index = latest.index.floor('s')
            start = latest.iloc[-1]['timestamp']
        else:
            
            #startDT = dt.datetime.fromtimestamp(start).isoformat()
            
            #start_time = dt.datetime(1970, 1, 1)
                     
            #print(startDT)
            
            
            response = session.get_kline(category='linear', 
                                         symbol=symbol, 
                                         start=start*1000,
                                         limit=1000,
                                         interval=interval).get('result')
            latest = format_data(response)
            
            if not latest.empty:
                start = latest.timestamp[-1:].values[0]
                start_str = dt.datetime.fromtimestamp(start).isoformat(sep="T", timespec="milliseconds")
            else:
                MyFlask.app().logger.warn("None received")
        
        if not isinstance(latest, pd.DataFrame):
            break

        MyFlask.app().logger.info("received " + str(latest.size) + " records")
        
        time.sleep(0.2)
        
        
        
        if not symbol in dfs.keys():
            dfs[symbol] = latest
        else:
            dfs[symbol] = pd.concat([dfs[symbol], latest])
            #dfs[symbol].index.names = ['timestamp']
        
        added=True
        MyFlask.app().logger.info("Appended data.")
        if len(latest) == 1:
            break
    
    if added:
        dfs[symbol].drop_duplicates(subset=['timestamp'], keep='last', inplace=True)

        quotes_list = [
            Quote(d,o,h,l,c,v) 
            for d,o,h,l,c,v 
            in zip(dfs[symbol].index, dfs[symbol]['open'], dfs[symbol]['high'], dfs[symbol]['low'], dfs[symbol]['close'], dfs[symbol]['volume'])
        ]
        
        stoRsi = indicators.get_stoch_rsi(quotes_list, 14,14,3,1)        
        stoch_rsi = []
        signals = []
        for stochRSIResult in stoRsi:
            stoch_rsi.append(stochRSIResult.stoch_rsi)
            signals.append(stochRSIResult.signal)

        dfs[symbol]['stoRsi'] = stoch_rsi
        dfs[symbol]['stoSignal'] = signals
        dfs[symbol] = dfs[symbol].fillna(0)
        
        dfs.get(symbol).to_csv(dataPath)

# try load data
#crte = Crta[]

def gmail(message, symbol):
    global creds, app
    gmailEmail = creds['gmailEmail']
    gmailPwd = creds['gmailPwd']


    try:
        MyFlask.app().logger.info('sending email...')
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
        MyFlask.app().logger.info('sending email...Done.')
    except:
        MyFlask.app().logger.error("failed to send mail")
        MyFlask.app().logger.error(traceback.format_exc())


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



def calculateCrossSections(symbol, crteD):
    dfs = read('dfs')
    
    logging.info("Calculating crossection...")
    krogci_x=[]
    krogci_y=[]
    krogci_radius=[]
    precision = 1e-15
    for index, row in dfs[symbol].tail(50).iterrows():
        loc = dfs[symbol].index.get_loc(row.name)
        try:
            
            seg_1_x1 = dfs[symbol].iloc[loc].timestamp
            seg_1_y1 = dfs[symbol].iloc[loc].low
            seg_1_x2 = dfs[symbol].iloc[loc].timestamp
            seg_1_y2 = dfs[symbol].iloc[loc].high

            point_1 = Point([seg_1_x1, seg_1_y1]) # x, y
            point_2 = Point([seg_1_x2, seg_1_y2]) # x, y
            line1 = LineString((point_1, point_2))
            
            set_precision(line1, precision)
            
            for crta1 in Crta.get_crteDforSymbol(symbol, crteD):
                #print(crta1.ime)
                if crta1.x0 != '' and crta1.x1 != '': 
                    #seg_2_x1 = crta1.convertTimeToValue(crta1.x0)
                    seg_2_x1 = crta1.x0_timestamp/1000
                    #time1 = dt.datetime.utcfromtimestamp(seg_2_x1/1000).strftime("%Y-%m-%d %H:%M:%S")
                    #print(time1)
                    seg_2_y1 = crta1.y0
                    #seg_2_x2 = crta1.convertTimeToValue(crta1.x1)
                    seg_2_x2 = crta1.x1_timestamp/1000
                    #time2 = dt.datetime.utcfromtimestamp(seg_2_x2/1000).strftime("%Y-%m-%d %H:%M:%S")
                    #print(time2)
                    seg_2_y2 = crta1.y1
    
                    point_3 = Point([seg_2_x1, seg_2_y1]) # x, y
                    point_4 = Point([seg_2_x2, seg_2_y2]) # x, y
                    line2 = LineString((point_3, point_4))
                    set_precision(line2, precision)
    
                    if line1.intersects(line2):
                        p_intersect = line1.intersection(line2)
                        x = p_intersect.x
                        y = p_intersect.y
                        #if(y<=seg_1_y2 and y>=seg_1_y1 and x>=seg_2_x1 and x<=seg_2_x2):
                        time = datetime.utcfromtimestamp(x).strftime("%Y-%m-%d %H:%M:%S")
                        krogci_x.append(time)
                        krogci_y.append(y)
                        krogci_radius.append(14)
                        #continue
        except Exception as e:
            MyFlask.app().logger.error("An exception occurred in calculateCrossSections:" + e.args)
            MyFlask.app().logger.error(traceback.format_exc())
            
    
    MyFlask.app().logger.info("Calculating crossection...Done.")
    return krogci_x, krogci_y, krogci_radius

def repeatPullNewData():
    dfs = read('dfs')
    crteD = read('crteD')
    global currentHour
    
    if currentHour==None or datetime.now().hour != currentHour:
        currentHour = datetime.now().hour
        MyFlask.app().logger.info("beep - hour changed: " + str(currentHour))
        try:
            for symbol in symbols.union(stocks):
                start = int(get_last_timestamp(symbol, dfs))
                dt = datetime.fromtimestamp(start, pytz.utc)
                MyFlask.app().logger.info("Datetime of last entry for " + symbol + " : " + dt.strftime('%Y-%m-%d %H:%M:%S'))
    
                pullNewData(symbol, start, dfs)
                
                krogci_x, krogci_y, krogci_radius = calculateCrossSections(symbol, crteD)
                sendMailForLastCrossSections(symbol, krogci_x, krogci_y)
            write('dfs', dfs)
        except:
            MyFlask.app().logger.error('Something went wrong retrieving data')
            MyFlask.app().logger.error(traceback.format_exc())

            
    
    threading.Timer(20, repeatPullNewData).start()

# function to create threads
def threaded_function():
    repeatPullNewData()

def initialCheckOfData():
    
    dfs = {}
#        f = lambda x: dt.datetime.utcfromtimestamp(int(x)/1000)
    for symbol in symbols.union(stocks):
        dataPath = getDataPath(symbol) + os.sep + symbol + '.data'            
        if not symbol in dfs.keys():
            if os.path.isfile(dataPath):
                MyFlask.app().logger.info("initialCheckOfData for: " + symbol)                
                df = pd.read_csv(dataPath, dtype={'timestamp': float}, thousands=',', decimal='.')
                MyFlask.app().logger.info("initialCheckOfData for: " + symbol + "--1")                
                
                f = lambda x: pd.Timestamp(x)
                df.index = pd.to_datetime(df['datetime'], utc=True, format='ISO8601')
                df.index.names = ['datetime'] 
                df.drop(['datetime'], axis=1, inplace=True)
                MyFlask.app().logger.info("initialCheckOfData for: " + symbol + "--2")                
                
                dfs[symbol] = df
                MyFlask.app().logger.info("initialCheckOfData for: " + symbol + "--3")                
    
    for symbol in symbols.union(stocks):
        MyFlask.app().logger.info("Checking freshness of data: " + symbol + " ...")
        start = get_last_timestamp(symbol, dfs)
        last_dt = datetime.fromtimestamp(start)
        duration = 0
        if symbol in symbols:
            duration = (datetime.now() - last_dt).total_seconds() / 3600
            if duration > 1:
                MyFlask.app().logger.info(str(duration) + " hours old data for " + symbol) 
                pullNewData(symbol, start, dfs)    
        elif symbol in stocks:
            duration = datetime.now() - last_dt
            if duration.days > 1:
                MyFlask.app().logger.info(str(duration.days) + " days old data for " + symbol) 
                pullNewData(symbol, start, dfs)    
    MyFlask.app().logger.info("Checking done.")

    MyFlask.app().logger.info("writing dfs data")                
    write('dfs', dfs)


    '''
    print('last values')
    print(dfs.get('BTCUSDT').timestamp[-1:].values[0])
    print(dfs.get('TSLA').timestamp[-1:].values[0])

    dfs = read('dfs')

    print('last values')
    print(dfs.get('BTCUSDT').timestamp[-1:].values[0])
    print(dfs.get('TSLA').timestamp[-1:].values[0])
    '''
    
    # load crte
    crteD = { }
    for symbol in symbols.union(stocks):
        crtePath = getDataPath(symbol) + os.sep + "crte.data"
        MyFlask.app().logger.info(crtePath)
        if os.path.isfile(crtePath):
            with open(crtePath, 'r') as f:
                json_str = f.read()
                crteForSymb = jsonpickle.decode(json_str)
                for crta in crteForSymb:
                    if crta.symbol == '':
                        crta.symbol = symbol
                    crteD[crta.ime]=crta   
    
    write('crteD', crteD)
    
    currentHour = dt.datetime.now().hour
    thread = Thread(target = threaded_function, args = ())
    thread.start()









