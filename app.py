#https://flask.palletsprojects.com/en/3.0.x/installation/
# pip install -r requirements.txt
#flask run
#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
# test
# https://blog.miguelgrinberg.com/post/running-your-flask-application-over-https
from flask import Flask, redirect, render_template, request, send_from_directory
from stock_indicators import indicators
from stock_indicators import Quote
from flask import abort
from threading import Thread
from flask_debug import Debug
import os.path
import pathlib
import traceback
import sys
from Crta import Crta
import re
from intersect import line_intersection, crosses
import logging
import locale
from shapely.geometry import LineString, Point
from shapely import set_precision
from shapely import distance
from threading import Thread, Lock

import numpy as np
import claudeTest
import yfinance as yahooFinance
import sys
from decimal import Decimal, getcontext

from matplotlib import image 
from matplotlib import pyplot as plt 

from pybit.unified_trading import HTTP
from pybit.unified_trading import WebSocket

import pandas as pd
import datetime as dt
from datetime import timedelta
import time, threading
import json
import jsonpickle
from typing import List
import pybit

from datetime import datetime, timezone, tzinfo
import pytz
from email.mime.multipart import MIMEMultipart
from email.mime.text import MIMEText
from email.mime.image import MIMEImage
import smtplib
from pathlib import Path
from string import Template
from numpy.distutils.fcompiler import none
from claudeTest import getSuggestion
#from tkinter.constants import CURRENT
#from pandas.conftest import datapath
global lineCounter, dfs, interval, crteD


app = Flask(__name__,
            static_folder='./static',
            template_folder='./templates')


crteD = dict()
dfs = dict()
claudRecomendation = dict()

lock = Lock()


symbols = {'BTCUSDT', 'ETHUSDT', 'SOLUSDT', 'ADAUSDT', 'MKRUSDT', 'JUPUSDT', 'RNDRUSDT', 'DOGEUSDT', 'HNTUSDT', 'BCHUSDT'}
stocks = {'TSLA', 'MSTR', 'GC=F', 'CLSK'}

supply = 2100000

lineCounter=0
dfs={}
interval = 60
locale.setlocale(locale.LC_ALL, 'sl_SI')


fig = plt.figure()  # the figure will be reused later

session = None
if os.path.isfile("./authcreds.json"):
    with open("./authcreds.json") as j:
        creds = json.load(j)
    
    kljuc = creds['kljuc']
    geslo = creds['geslo']

    session = HTTP(api_key=kljuc, api_secret=geslo, testnet=False)

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

def getDataPath(symbol):
        path = pathlib.Path("." + os.sep + symbol).resolve()
        if not (os.path.isdir(path)):
            os.mkdir(path, mode = 0o777)
            app.logger.info("Directory '% s' created" % path)
        return os.path.realpath(path);
    
def get_last_timestamp(symbol):
    if not symbol in dfs.keys():
        return int(dt.datetime(2009, 1, 1).timestamp()* 1000)
        #return int(dt.datetime(2024, 1, 1).timestamp()* 1000)

    return int(dfs.get(symbol).timestamp[-1:].values[0])
    

def pullNewData(symbol, start, interval):
    global dfs
    added = False
    
    dataPath = getDataPath(symbol) + os.sep + symbol + '.data'
    
    while True:
        app.logger.info(dt.datetime.now(pytz.timezone('Europe/Ljubljana')).strftime("%d.%m.%Y %H:%M:%S") + \
            ' Collecting data for: ' + symbol + ' from ' + \
            dt.datetime.fromtimestamp(start/1000).strftime("%d.%m.%Y %H:%M:%S"))

        if symbol in stocks:
            if start==1230764400000:
                start = int(dt.datetime(2020, 1, 1).timestamp()* 1000)
            stock = yahooFinance.Ticker(symbol)
            startFrom = dt.datetime.fromtimestamp(start/1000).strftime("%Y-%m-%d")
            endFromDt = dt.datetime.fromtimestamp(start/1000) + timedelta(days=350)
            if endFromDt>dt.datetime.now():
                endFromDt=dt.datetime.now()
            endFrom = endFromDt.strftime("%Y-%m-%d")
            response = stock.history(start=startFrom, end=endFrom, interval='1d')
            latest = format_data(response)
            
            latest = latest.rename_axis("timestamp")
            latest.index = latest.index.tz_convert(None)
            latest = latest.sort_index(inplace=False)
            
            latest.index = latest.index.floor('s')
            
            start = latest.iloc[-1]['timestamp']
        else:
            response = session.get_kline(category='linear', 
                                         symbol=symbol, 
                                         start=start,
                                         interval=interval).get('result')
            latest = format_data(response)
            start = latest.timestamp[-1:].values[0]
        
        app.logger.info("received " + str(latest.size) + " records")
        
        if not isinstance(latest, pd.DataFrame):
            break
        
        time.sleep(0.2)
        
        if not symbol in dfs.keys():
            dfs[symbol] = latest
        else:
            dfs[symbol] = pd.concat([dfs[symbol], latest])
            
        added=True
        app.logger.info("Appended data.")
        if len(latest) == 1:
            break
    
    if added:
        
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

        dfs.get(symbol).drop_duplicates(subset=['timestamp'], keep='last', inplace=True)

        dfs.get(symbol).to_csv(dataPath)
        
        app.logger.info("Saved to csv.")

# try load data
jsonpickle.set_encoder_options('json', sort_keys=True, indent=4)

for symbol in symbols.union(stocks):
    dataPath = getDataPath(symbol) + os.sep + symbol + '.data'            
    if not symbol in dfs.keys():
        if os.path.isfile(dataPath):
            dfs[symbol] = pd.read_csv(dataPath)
            dfs[symbol] = dfs[symbol].drop(['timestamp'], axis=1)
            dfs[symbol] = dfs[symbol].rename(columns={"timestamp.1": "timestamp"})
            f = lambda x: dt.datetime.utcfromtimestamp(int(x)/1000)
            dfs[symbol].index = dfs[symbol].timestamp.apply(f)

            
#crte = Crta[]

def gmail(message, symbol):
    global creds
    gmailEmail = creds['gmailEmail']
    gmailPwd = creds['gmailPwd']


    try:
        app.logger.info('sending email...')
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
        app.logger.info('sending email...Done.')
    except:
        app.logger.error("failed to send mail")
        app.logger.error(traceback.format_exc())

'''
message = MIMEMultipart("alternative")
part1 = MIMEText("testing", "plain")
message.attach(part1)
gmail(message)
'''

def obv(data):
    """
    Calculate On Balance Volume (OBV) for given data.
    
    :param data: pandas DataFrame which contains ['Close', 'Volume'] columns
    :return: pandas Series with OBV values
    """
    obv = [0]
    for i in range(1, len(data)):
        if data['Close'][i] > data['Close'][i - 1]:
            obv.append(obv[-1] + data['Volume'][i])
        elif data['Close'][i] < data['Close'][i - 1]:
            obv.append(obv[-1] - data['Volume'][i])
        else:
            obv.append(obv[-1])
    return pd.Series(obv, index=data.index)


'''
# test retrieving of tsla and btcusdt
testSymbols = ['TSLA', 'BTCUSDT']
for symbol in testSymbols:
    start = int(dt.datetime(2009, 1, 1).timestamp()* 1000)
    if symbol in dfs.keys():
        claudRecomendation[symbol] = getSuggestion(dfs[symbol])
        start = get_last_timestamp(symbol)
    else:
        claudRecomendation[symbol] = ""
    
    pullNewData(symbol, start, interval)
sys.exit(0)    
# test retrieving of tsla and btcusdt
'''

if session != None:
    result = session.get_tickers(category="linear").get('result')['list']
    # if (asset['symbol'].endswith('USDT') or asset['symbol'].endswith('BTC'))]
    tickers = [asset['symbol'] for asset in result]
    app.logger.info(tickers)
    tickers_data=""


def initialCheckOfData():
    for symbol in symbols.union(stocks):
        crtePath = getDataPath(symbol) + os.sep + "crte.data"
        app.logger.info(crtePath)
        if os.path.isfile(crtePath):
            with open(crtePath, 'r') as f:
                json_str = f.read()
                crteD[symbol] = jsonpickle.decode(json_str)
        else:
            crte: List[Crta] = []
            crteD[symbol] = crte
        start = int(dt.datetime(2009, 1, 1).timestamp()* 1000)
        if symbol in dfs.keys():
            start = get_last_timestamp(symbol)
            last_dt = datetime.fromtimestamp(start/1000)
            duration = 0
            if symbol in symbols:
                duration = (datetime.now() - last_dt).total_seconds() / 3600
                if duration > 1:
                    app.logger.info(str(duration) + " hours old data for " + symbol) 
                    pullNewData(symbol, start, interval)    
            elif symbol in stocks:
                duration = datetime.now() - last_dt
                if duration.days > 1:
                    app.logger.info(str(duration.days) + " days old data for " + symbol) 
                    pullNewData(symbol, start, interval)    
                
threading.Timer(0,initialCheckOfData).start() 
    

def sendMailForLastCrossSections(symbol, krogci_x, krogci_y):
    i=0;
    text_data='';
    for x in krogci_x:
        text_data = text_data + \
                'time:  ' + krogci_x[i] + '\n' + \
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



def intersection(X1, X2):
    x = np.union1d(X1[0], X2[0])
    y1 = np.interp(x, X1[0], X1[1])
    y2 = np.interp(x, X2[0], X2[1])
    dy = y1 - y2

    ind = (dy[:-1] * dy[1:] < 0).nonzero()[0]
    x1, x2 = x[ind], x[ind+1]
    dy1, dy2 = dy[ind], dy[ind+1]
    y11, y12 = y1[ind], y1[ind+1]
    y21, y22 = y2[ind], y2[ind+1]

    x_int = x1 - (x2 - x1) * dy1 / (dy2 - dy1)
    y_int = y11 + (y12 - y11) * (x_int - x1) / (x2 - x1)
    return x_int, y_int


def calculateCrossSections(symbol):
    app.logger.info("Calculating crossection...")
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
            
            x1 = np.array([seg_1_x1,seg_1_x2], dtype=float)
            y1 = np.array([seg_1_y1,seg_1_y2], dtype=float)


            
            set_precision(line1, precision)
            
            if len(crteD[symbol])>0:
                for crta in crteD[symbol]:
                    #print(crta.ime)
                    
                    if crta.x0 != '' and crta.x1 != '': 
                        seg_2_x1 = crta.convertTimeToValue(crta.x0)
                        time1 = dt.datetime.utcfromtimestamp(seg_2_x1/1000).strftime("%Y-%m-%d %H:%M:%S")
                        #print(time1)
                        seg_2_y1 = crta.y0
                        seg_2_x2 = crta.convertTimeToValue(crta.x1)
                        time2 = dt.datetime.utcfromtimestamp(seg_2_x2/1000).strftime("%Y-%m-%d %H:%M:%S")
                        #print(time2)
                        seg_2_y2 = crta.y1
        
                        point_3 = Point([seg_2_x1, seg_2_y1]) # x, y
                        point_4 = Point([seg_2_x2, seg_2_y2]) # x, y
                        line2 = LineString((point_3, point_4))
                        set_precision(line2, precision)
        
                        x2 = np.array([seg_2_x1,seg_2_x2], dtype=float)
                        y2 = np.array([seg_2_y1,seg_2_y2], dtype=float)
        
                        if line1.intersects(line2):
                            p_intersect = line1.intersection(line2)
                            x = p_intersect.x
                            y = p_intersect.y
                            #if(y<=seg_1_y2 and y>=seg_1_y1 and x>=seg_2_x1 and x<=seg_2_x2):
                            time = dt.datetime.utcfromtimestamp(x/1000).strftime("%Y-%m-%d %H:%M:%S")
                            krogci_x.append(time)
                            krogci_y.append(y)
                            krogci_radius.append(10)
                            #continue
        except Exception as e:
            app.logger.error("An exception occurred in calculateCrossSections.")
            app.logger.error(traceback.format_exc())
            
    
    app.logger.info("Calculating crossection...Done.")
    return krogci_x, krogci_y, krogci_radius




#response = session.get_kline(category='linear', 
#                             symbol=mysymbol, 
#                             interval='D').get('result')
#df = format_data(response)
# https://bybit-exchange.github.io/docs/v5/websocket/public/kline
'''
ws = WebSocket(
    testnet=True,
    channel_type="linear",
    api_key=kljuc,
    api_secret=geslo,
    trace_logging=False,
)

def handle_message(messageDict):
    global df
    data = messageDict["data"][0]
    if data['confirm'] == True:
        print(df)
        try:
            x = messageDict['data'][0]['timestamp']
            timestamp = dt.datetime.utcfromtimestamp(int(x)/1000)
            df2 = pd.DataFrame({'timestamp': data['timestamp'],\
                                'open': data['open'],\
                                'high': data['high'],\
                                'low': data['low'],\
                                'close': data['close'],\
                                'volume': data['volume'],\
                                'turnover': data['turnover']},\
                                index=[0])
            #df = pd.concat([df,df2],axis=1)
            f = lambda x: dt.datetime.utcfromtimestamp(int(x)/1000)
            df2.index = df2.timestamp.apply(f)
            df = pd.concat([df, df2])
            dt_now = datetime.now(pytz.timezone('Europe/Ljubljana')) 
            
            print(dt_now, " appended data " + timestamp.strftime('%Y-%m-%d %H:%M:%S'))
            df.to_csv(dataPath)
        
        
        except:
            print(traceback.format_exc())



# interval
# 1 3 5 15 30 60 120 240 360 720 minute
# D day
# W week
# M month
ws.kline_stream(
    interval='1',  # 5 minute, https://bybit-exchange.github.io/docs/v5/enum#interval
    symbol= mysymbol, # "BTCUSDT",
    callback=handle_message,
)
'''

currentHour = dt.datetime.now().hour
def repeatPullNewData():
    global currentHour, symbols
    if dt.datetime.now().hour != currentHour:
        currentHour = dt.datetime.now().hour
        app.logger.info("beep - hour changed: " + str(currentHour))
        try:
            for symbol in symbols.union(stocks):
                start = int(dt.datetime(2009, 1, 1).timestamp()* 1000)
                #start = int(dt.datetime(2024, 1, 1).timestamp()* 1000)
                if symbol in dfs.keys():
                    claudRecomendation[symbol] = getSuggestion(dfs[symbol])
                    start = get_last_timestamp(symbol)
                else:
                    claudRecomendation[symbol] = ""
    
                pullNewData(symbol, start, interval)
                
                krogci_x, krogci_y, krogci_radius = calculateCrossSections(symbol)
                sendMailForLastCrossSections(symbol, krogci_x, krogci_y)
        except:
            app.logger.error('Something went wrong retrieving data')
            app.logger.error(traceback.format_exc())

            
    
    threading.Timer(20, repeatPullNewData).start()
    
    
# function to create threads
def threaded_function():
    repeatPullNewData()
 
 
thread = Thread(target = threaded_function, args = ())
thread.start()
thread.join()
print("thread finished...exiting")
    


def getCrtaWithIndex(index, symbol):
    i=0
    if symbol in crteD.keys():
        for crta in crteD[symbol]:
            if i==index:
                return crta
            i=i+1
    return None

def getNextIndex(symbol):
    ret=0
    if symbol in crteD.keys():
        if len(crteD[symbol])>0:
            for crta in crteD[symbol]:
                if ret < crta.i:
                    ret = crta.i
            ret = ret + 1
    return ret

def getPlotData(symbol):
    global crteD
    #df['time'] = df['timestamp'].apply(lambda x: str(x)[14:4])
    #f = lambda x: dt.datetime.utcfromtimestamp(int(x)/1000)
    #df['time'] = df['timestamp'].apply(f)
    #x = df['time'].apply(lambda x: int(x)).tolist()
    #x = df['timestamp'].index.astype("str").tolist()
    howmany = 2000
    
    x = dfs[symbol].tail(howmany).index.astype("str").tolist()
    open_ = dfs[symbol].tail(howmany)['open'].astype(float).tolist()
    high = dfs[symbol].tail(howmany)['high'].astype(float).tolist()
    low = dfs[symbol].tail(howmany)['low'].astype(float).tolist()
    close = dfs[symbol].tail(howmany)['close'].astype(float).tolist()
    volume = dfs[symbol].tail(howmany)['volume'].astype(float).tolist()
    
    ind1 = dfs[symbol].tail(howmany)['stoRsi'].astype(float).tolist()
    signal = dfs[symbol].tail(howmany)['stoSignal'].astype(float).tolist()

    lines = [];
    if symbol in crteD.keys():
        for crta in crteD[symbol]:
            lines.append(crta.plotlyLine());
            
    krogci_x, krogci_y, krogci_radius = calculateCrossSections(symbol)

    return {'x_axis': x, 'open': open_, 'high': high, 'low': low, 'close': close, 'volume': volume, 'lines': lines, 
            'ind1_sto': ind1,
            'ind1_signal': signal,
            'title': symbol, 
            'krogci_x': krogci_x, 'krogci_y': krogci_y, 'krogci_radius': krogci_radius,
            'range_start': dfs[symbol].iloc[-int(howmany/2)].name, 'range_end': dfs[symbol].iloc[-1].name + timedelta(days=7)
            }
    

@app.errorhandler(Exception)
def all_exception_handler(error):
    app.logger.error(str(error))
    app.logger.error(traceback.format_exc())
    

@app.route('/scroll', methods=['POST'])
def scroll():
    global crteD
    
    symbol = request.args.get('pair')
    if symbol==None:
        symbol = "BTCUSDT"
        
    contentJson = request.json
    app.logger.info(contentJson)

    xaxis0 = contentJson['xaxis.range[0]'];
    xaxis1 = contentJson['xaxis.range[1]'];
    
    if "." in xaxis0:
        xaxis0_ = (datetime.strptime(xaxis0, "%Y-%m-%d %H:%M:%S.%f"))
    else:
        xaxis0_ = (datetime.strptime(xaxis0, "%Y-%m-%d %H:%M:%S"))
        
    if "." in xaxis1:
        xaxis1_ = (datetime.strptime(xaxis1, "%Y-%m-%d %H:%M:%S.%f"))
    else:
        xaxis1_ = (datetime.strptime(xaxis1, "%Y-%m-%d %H:%M:%S"))
    


    xaxis0_ = xaxis0_.strftime('%Y-%m-%d %H:00:00')
    xaxis1_ = xaxis1_.strftime('%Y-%m-%d %H:00:00')
    
    df_range = dfs[symbol].loc[pd.Timestamp(xaxis0_):pd.Timestamp(xaxis1_)]
    
    x = df_range.index.astype("str").tolist()
    open_ = df_range['open'].astype(float).tolist()
    high = df_range['high'].astype(float).tolist()
    low = df_range['low'].astype(float).tolist()
    close = df_range['close'].astype(float).tolist()
    volume = df_range['volume'].astype(float).tolist()
    lines = [];
    for crta in crteD[symbol]:
        lines.append(crta.plotlyLine());
    
    krogci_x, krogci_y, krogci_radius = calculateCrossSections(symbol)
    
    return {'x_axis': x, 'open': open_, 'high': high, 'low': low, 'close': close, 'volume': volume,'lines': lines, 'title': symbol, 
            'krogci_x': krogci_x, 'krogci_y': krogci_y, 'krogci_radius': krogci_radius,
           }, 200
    

def writeCrte(symbol):
    crtePath = getDataPath(symbol) + os.sep + "crte.data"
    try:
        with open(crtePath,'w') as f:
            strJson = jsonpickle.encode(crteD[symbol], indent=2)
            f.write(strJson)
            app.logger.info("Wrote crte for symbol: " + symbol)
             
    except:
        if os.path.isfile(crtePath):        
            os.remove(crtePath)
        app.logger.error(traceback.format_exc())
        # or
        app.logger.info(sys.exc_info()[2])      


@app.route('/deleteLine', methods=['POST'])
def deleteLine():
    '''
    remote_ip = request.headers.get('X-Forwarded-For')
    if remote_ip != '89.233.122.140':
        return "forbidden", 403
    '''
    symbol = request.args.get('pair')
    if symbol==None:
        symbol = "BTCUSDT"
            
    line_name = request.args.get('name')
    app.logger.info("Delete line for symbol: " + symbol + " with name: " + line_name)
    for crta in crteD[symbol]:
        if crta.ime == line_name:
            app.logger.info("Delete line with name: " + line_name + " on symbol: " + symbol)
            app.logger.info("Length before: " + str(len(crteD[symbol])))
            crteD[symbol].remove(crta);
            app.logger.info("Length after:  " + str(len(crteD[symbol])))
            writeCrte(symbol)

    app.logger.info("Delete line for symbol: "+symbol+" ...Done.")
    return getPlotData(symbol), 200

@app.route('/addLine', methods=['POST'])
def addLine():
    global crteD
    '''
    remote_ip = request.headers.get('X-Forwarded-For')
    if remote_ip != '89.233.122.140':
        return "forbidden", 403
    '''
        
    symbol = request.args.get('pair')
    if symbol==None:
        symbol = "BTCUSDT"
    
    app.logger.info("/addLine for symbol: " + symbol)
            
    contentJson = request.json
    app.logger.info(contentJson)

    crtePath = getDataPath(symbol) + os.sep + "crte.data"
    
    if 'type' in contentJson.keys() and contentJson['type']=='line':
        crta=Crta(getNextIndex(symbol), contentJson['x0'], contentJson['y0'], contentJson['x1'], contentJson['y1'])
        crteD[symbol].append(crta) 
        writeCrte(symbol)
        app.logger.info("Wrote new line for symbol: " + symbol + " " + crta.ime);
        return getPlotData(symbol), 200
    elif list(contentJson.keys())[0].startswith("shapes"):
        app.logger.info("Correcting one line...")
        x = re.search(r"shapes\[(.*)\].*", list(contentJson.keys())[0])
        strI = x.group(1)
        app.logger.info("Correcting one line... strI: " + strI)
        intI=int(strI)
        app.logger.info("Correcting one line... strI: " + str(intI))
        crta = getCrtaWithIndex(intI, symbol)
        if not crta is None:
            if 'shapes['+strI+'].x0' in list(contentJson.keys()):
                crta.changeX0(contentJson['shapes['+strI+'].x0'])
            if 'shapes['+strI+'].y0' in list(contentJson.keys()):
                crta.y0 = contentJson['shapes['+strI+'].y0']
            if 'shapes['+strI+'].x1' in list(contentJson.keys()):
                crta.changeX1(contentJson['shapes['+strI+'].x1'])
            if 'shapes['+strI+'].y1' in list(contentJson.keys()):
                crta.y1 = contentJson['shapes['+strI+'].y1']
            writeCrte(symbol)
            return getPlotData(symbol), 200
        else:
            app.logger.warn("Did not find crta: " + str(intI))
    else:
        app.logger.warn("Unknown json: " + contentJson)

    app.logger.info("/addLine for symbol: " + symbol + "... Done.")
    return "ok", 200

'''
@app.route('/favicon.ico')
def favicon():
    print(os.path.join(app.root_path, 'static'))
    return send_from_directory(app.static_folder, 'favicon.ico') 
'''    
def threaded_function2(symbol, start, interval):
    pullNewData(symbol, start, interval)
 
thread2 = Thread()

'''
@app.errorhandler(404)
def page_not_found(error):
    return render_template('./404.html'), 404
'''

@app.route('/',methods = ['GET'])
def root():
    return redirect("/index.html", code=302)
    #return render_template('./404.html'), 404

@app.route('/index.html')
def index():
    global thread2
    symbol = request.args.get('pair')
    if(symbol == None or symbol==""):
        symbol = "BTCUSDT"
    
    mydata = getDataPath(symbol) + os.sep + symbol + ".data"
    if not os.path.isfile(mydata):
        start = int(dt.datetime(2009, 1, 1).timestamp()* 1000)
        if thread2.is_alive():
            return "Thread for collecting data is running... Try later..."
        else:
            thread2 = Thread(target = threaded_function2, args = (symbol, start, interval))
            thread2.start()
            return "Thread for collecting data has been started... Try later..."
        
    else:
        if not symbol in dfs.keys():
            dfs[symbol] = pd.read_csv(mydata)
            dfs[symbol] = dfs[symbol].drop(['timestamp'], axis=1)
            dfs[symbol] = dfs[symbol].rename(columns={"timestamp.1": "timestamp"})
            f = lambda x: dt.datetime.utcfromtimestamp(int(x)/1000)
            dfs[symbol].index = dfs[symbol].timestamp.apply(f)
    
    app.logger.info(dfs[symbol])
    plot_data1 = getPlotData(symbol)
    
    tickers_data = " "
    for symb in symbols.union(stocks):
        tickers_data = tickers_data + '<option value="'+symb+'">'+symb+'</option>'    
    
    claudRecomendation[symbol] = getSuggestion(dfs[symbol])
    if claudRecomendation[symbol] != None and len(claudRecomendation[symbol])>0:
        return render_template('./index.html', plot_data=plot_data1, 
                               webpage_data={'tickers_data': tickers_data, 'selectedPair': symbol, 'suggestion': claudRecomendation[symbol][0], 'explanation': claudRecomendation[symbol][1]
                                            , 'price': f"{claudRecomendation[symbol][2]:,.2f}", 'datetime': claudRecomendation[symbol][3]})


    return render_template('./index.html', plot_data=plot_data1, 
                           webpage_data={'tickers_data': tickers_data, 'selectedPair': symbol})

@app.route('/favicon.ico')
def favicon():
    return send_from_directory(os.path.join(app.root_path, 'static'),
                               'favicon.ico', mimetype='image/vnd.microsoft.icon')

#Debug(app)
#app = Flask(__name__)
#app.conf['DEBUG'] = True
    
if __name__ != '__main__':
    gunicorn_logger = logging.getLogger('gunicorn.error')
    app.logger.handlers = gunicorn_logger.handlers
    app.logger.setLevel(gunicorn_logger.level)
else:
    app.logger.setLevel(logging.INFO)  # Set log level to INFO
    #handler = logging.FileHandler('app.log')  # Log to a file
    handlerConsole = logging.StreamHandler(sys.stdout)
    #app.logger.addHandler(handler)
    app.logger.addHandler(handlerConsole)    
    app.run(host = '127.0.0.1', port = '8000', debug=True, threaded=False)

app.config['SEND_FILE_MAX_AGE_DEFAULT'] = 0
