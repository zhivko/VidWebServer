
#https://flask.palletsprojects.com/en/3.0.x/installation/
# pip install -r requirements.txt
#flask run
#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
# test
# https://blog.miguelgrinberg.com/post/running-your-flask-application-over-https
from flask import current_app, Flask, redirect, render_template, request, send_from_directory
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
import sys
from decimal import Decimal, getcontext

from matplotlib import image 
from matplotlib import pyplot as plt 

import pandas as pd
import datetime as dt
from datetime import timedelta
import time, threading
import json
import jsonpickle
from typing import List
import pybit

from datetime import datetime, timezone
from zoneinfo import ZoneInfo
from pathlib import Path
from string import Template
from numpy.distutils.fcompiler import none
from claudeTest import getSuggestion
#from tkinter.constants import CURRENT
#from pandas.conftest import datapath
#global lineCounter, dfs, interval, crteD

from DataStorageSingleton import DataStorageSingleton


dataStorageSingleton: DataStorageSingleton

app = Flask(__name__,
            static_folder='./static',
            template_folder='./templates')

claudRecomendation = dict()


supply = 2100000

locale.setlocale(locale.LC_ALL, 'sl_SI')


fig = plt.figure()  # the figure will be reused later

def utc_to_milliseconds(utc_string):
    # Parse the UTC string into a datetime object
    utc_datetime = datetime.strptime(utc_string, "%Y-%m-%dT%H:%M:%S.%fZ")
    
    # Calculate the timestamp in milliseconds
    timestamp_ms = int(utc_datetime.timestamp() * 1000)
    
    return timestamp_ms



def getDataPath(symbol):
        path = pathlib.Path("." + os.sep + symbol).resolve()
        if not (os.path.isdir(path)):
            os.mkdir(path, mode = 0o777)
            app.logger.info("Directory '% s' created" % path)
        return os.path.realpath(path);
    

# try load data
#crte = Crta[]


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




    




def intersection(X1, X2):
    x = np.union1d(X1[0], X2[0])
    y1 = np.interp(x, X1[0], X1[1])
    y2 = np.interp(x, X2[0], X2[1])
    dy = y1 - y2

    ind = (dy[:-1] * dy[1:] < 0).nonzero()[0]
    x1, x2 = x[ind], x[ind+1]
    dy1, dy2 = dy[ind], dy[ind+1]
    y11, y12 = y1[ind], y1[ind+1]
    x_int = x1 - (x2 - x1) * dy1 / (dy2 - dy1)
    y_int = y11 + (y12 - y11) * (x_int - x1) / (x2 - x1)
    return x_int, y_int





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


    
    


    


def getCrtaWithIndex(index, symbol):
    i=0
    if symbol in dataStorageSingleton.get_crteD().keys():
        for crta in dataStorageSingleton.get_crteD()[symbol]:
            if i==index:
                return crta
            i=i+1
    return None

def writeCrtaWithIndex(index, symbol, crta: Crta):
    i=0
    if symbol in dataStorageSingleton.get_crteD().keys():
        for crta1 in dataStorageSingleton.get_crteD()[symbol]:
            if index==crta1.i:
                crta1 = crta
                #dataStorageSingleton.get_crteD()[symbol][i] = crta
                break
            i=i+1
            
            
    for crta in dataStorageSingleton.get_crteD()[symbol]:
        print(crta.plotlyLine());
            
    return None

def getNextIndex(symbol):
    ret=0
    if symbol in dataStorageSingleton.get_crteD().keys():
        if len(dataStorageSingleton.get_crteD()[symbol])>0:
            for crta in dataStorageSingleton.get_crteD()[symbol]:
                if ret < crta.i:
                    ret = crta.i
            ret = ret + 1
    return ret

def getPlotData(symbol):
    #df['time'] = df['timestamp'].apply(lambda x: str(x)[14:4])
    #f = lambda x: dt.datetime.utcfromtimestamp(int(x)/1000)
    #df['time'] = df['timestamp'].apply(f)
    #x = df['time'].apply(lambda x: int(x)).tolist()
    #x = df['timestamp'].index.astype("str").tolist()
    howmany = 2000
    
    x = dataStorageSingleton.get_dfs()[symbol].tail(howmany).index.astype('str').tolist()
    open_ = dataStorageSingleton.get_dfs()[symbol].tail(howmany)['open'].astype(float).tolist()
    high = dataStorageSingleton.get_dfs()[symbol].tail(howmany)['high'].astype(float).tolist()
    low = dataStorageSingleton.get_dfs()[symbol].tail(howmany)['low'].astype(float).tolist()
    close = dataStorageSingleton.get_dfs()[symbol].tail(howmany)['close'].astype(float).tolist()
    volume = dataStorageSingleton.get_dfs()[symbol].tail(howmany)['volume'].astype(float).tolist()
    
    ind1 = dataStorageSingleton.get_dfs()[symbol].tail(howmany)['stoRsi'].astype(float).tolist()
    signal = dataStorageSingleton.get_dfs()[symbol].tail(howmany)['stoSignal'].astype(float).tolist()

    lines = []
    for crta in dataStorageSingleton.get_crteDforSymbol(symbol):
        lines.append(crta.plotlyLine());
            
    krogci_x = []
    krogci_y = []
    krogci_radius = []
    try:
        krogci_x, krogci_y, krogci_radius = dataStorageSingleton.calculateCrossSections(symbol)
    except:
        print("Error calculating dataStorageSingleton.calculateCrossSections")
         
    
    dt1 = datetime.utcfromtimestamp(dataStorageSingleton.get_dfs()[symbol].iloc[-int(howmany/2)].timestamp/1000)
    dt2 = datetime.utcfromtimestamp(dataStorageSingleton.get_dfs()[symbol].iloc[-1].timestamp/1000)

    r_s = dt1.strftime("%Y-%m-%d %H:%M:%S");
    r_e = dt2.strftime("%Y-%m-%d %H:%M:%S");
    

    return {'x_axis': x, 'open': open_, 'high': high, 'low': low, 'close': close, 'volume': volume, 'lines': lines, 
            'ind1_sto': ind1,
            'ind1_signal': signal,
            'title': symbol, 
            'krogci_x': krogci_x, 'krogci_y': krogci_y, 'krogci_radius': krogci_radius,
            'range_start': r_s,
            'range_end': r_e
            }
    

@app.errorhandler(Exception)
def all_exception_handler(error):
    app.logger.error(str(error))
    app.logger.error(traceback.format_exc())
    
    
    
@app.route('/scroll', methods=['POST'])
def scroll():
    crteD=dataStorageSingleton.get_crteD()
    dfs=dataStorageSingleton.get_dfs()
    
    symbol = request.args.get('pair')
    if symbol==None:
        symbol = "BTCUSDT"
        
    contentJson = request.json
    app.logger.info(contentJson)

    xaxis0 = contentJson['xaxis.range[0]'];
    xaxis1 = contentJson['xaxis.range[1]'];
    
    if "." in xaxis0:
        xaxis0_ = (datetime.strptime(xaxis0, "%Y-%m-%d %H:%M:%S.%f"))
    elif len(xaxis0)==16:
        xaxis0_ = (datetime.strptime(xaxis0, "%Y-%m-%d %H:%M"))
    else:
        xaxis0_ = (datetime.strptime(xaxis0, "%Y-%m-%d %H:%M:%S"))
        
    if "." in xaxis1:
        xaxis1_ = (datetime.strptime(xaxis1, "%Y-%m-%d %H:%M:%S.%f"))
    elif len(xaxis1)==16:
        xaxis1_ = (datetime.strptime(xaxis1, "%Y-%m-%d %H:%M"))
    else:
        xaxis1_ = (datetime.strptime(xaxis1, "%Y-%m-%d %H:%M:%S"))
    


    xaxis0_ = xaxis0_.strftime('%Y-%m-%d %H:00:00')
    xaxis1_ = xaxis1_.strftime('%Y-%m-%d %H:00:00')
    
    df_range = dataStorageSingleton.get_dfs()[symbol].loc[pd.Timestamp(xaxis0_):pd.Timestamp(xaxis1_)]
    
    x = df_range.index.astype("str").tolist()
    open_ = df_range['open'].astype(float).tolist()
    high = df_range['high'].astype(float).tolist()
    low = df_range['low'].astype(float).tolist()
    close = df_range['close'].astype(float).tolist()
    volume = df_range['volume'].astype(float).tolist()
    lines = [];
    for crta in crteD[symbol]:
        lines.append(crta.plotlyLine());
    
    krogci_x, krogci_y, krogci_radius = dataStorageSingleton.calculateCrossSections(symbol)
    
    return {'x_axis': x, 'open': open_, 'high': high, 'low': low, 'close': close, 'volume': volume,'lines': lines, 'title': symbol, 
            'krogci_x': krogci_x, 'krogci_y': krogci_y, 'krogci_radius': krogci_radius,
           }, 200
    

@app.route('/deleteLine', methods=['POST'])
def deleteLine():
    dataStorageSingleton.get_crteD()
        
    symbol = request.args.get('pair')
    if symbol==None:
        symbol = "BTCUSDT"
            
    line_name = request.args.get('name')
    app.logger.info("Delete line for symbol: " + symbol + " with name: " + line_name)
    dataStorageSingleton.remove_crteD(dataStorageSingleton[line_name])

    app.logger.info("Delete line for symbol: "+symbol+" ...Done.")
    return getPlotData(symbol), 200

@app.route('/addLine', methods=['POST'])
def addLine():
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
        crta=Crta(getNextIndex(symbol), contentJson['x0'], contentJson['y0'], contentJson['x1'], contentJson['y1'], symbol)
        dataStorageSingleton.update_crteD(crta)
        dataStorageSingleton.writeCrte(crta.symbol)
        return getPlotData(symbol), 200
    elif list(contentJson.keys())[0].startswith("shapes"):
        app.logger.info("Correcting one line...")
        x = re.search(r"shapes\[(.*)\].*", list(contentJson.keys())[0])
        strI = x.group(1)
        intI=int(strI)
        crta=dataStorageSingleton.get_crteDforSymbol(symbol)[intI]
        app.logger.info("Correcting one line " + crta.ime + " strI: " + str(intI))
        if not crta is None:
            if 'shapes['+strI+'].x0' in list(contentJson.keys()):
                crta.changeX0(contentJson['shapes['+strI+'].x0'])
            if 'shapes['+strI+'].y0' in list(contentJson.keys()):
                crta.y0 = contentJson['shapes['+strI+'].y0']
            if 'shapes['+strI+'].x1' in list(contentJson.keys()):
                crta.changeX1(contentJson['shapes['+strI+'].x1'])
            if 'shapes['+strI+'].y1' in list(contentJson.keys()):
                crta.y1 = contentJson['shapes['+strI+'].y1']
            dataStorageSingleton.update_crteD(crta)
            dataStorageSingleton.writeCrte(crta.symbol)
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
    DataStorageSingleton._instance.pullNewData(symbol, start, interval)
 
thread2 = Thread()
app.config['thread2'] = thread2

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
            thread2 = Thread(target = threaded_function2, args = (symbol, start))
            thread2.start()
            return "Thread for collecting data has been started... Try later..."
        
    else:
        if not symbol in dataStorageSingleton.get_dfs().keys():
            dataStorageSingleton.get_dfs()[symbol] = pd.read_csv(mydata)
            dataStorageSingleton.get_dfs()[symbol] = dataStorageSingleton.get_dfs()[symbol].drop(['timestamp'], axis=1)
            dataStorageSingleton.get_dfs()[symbol] = dataStorageSingleton.get_dfs()[symbol].rename(columns={"timestamp.1": "timestamp"})
            f = lambda x: dt.datetime.utcfromtimestamp(int(x)/1000)
            dataStorageSingleton.get_dfs()[symbol].index = dataStorageSingleton.get_dfs()[symbol].timestamp.apply(f)
    
    app.logger.info(dataStorageSingleton.get_dfs()[symbol])
    plot_data1 = getPlotData(symbol)
    
    tickers_data = " "
    for symb in DataStorageSingleton._instance.symbols.union(dataStorageSingleton._instance.stocks):
        tickers_data = tickers_data + '<option value="'+symb+'">'+symb+'</option>'    
    
    claudRecomendation[symbol] = getSuggestion(dataStorageSingleton.get_dfs()[symbol])
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
#threadInitialCheck.join()

app.config['SEND_FILE_MAX_AGE_DEFAULT'] = 0


if __name__ != '__main__':
    gunicorn_logger = logging.getLogger('gunicorn.error')
    app.logger.handlers = gunicorn_logger.handlers
    app.logger.setLevel(gunicorn_logger.level)

    
if __name__ == '__main__':
    dataStorageSingleton = DataStorageSingleton(app)
    app.logger.setLevel(logging.INFO)  # Set log level to INFO
    #handler = logging.FileHandler('app.log')  # Log to a file
    #handlerConsole = logging.StreamHandler(sys.stdout)
    #app.logger.addHandler(handler)
    #app.logger.addHandler(handlerConsole)    


    app.run(host = '127.0.0.1', port = '8000', debug=False, threaded=False)
