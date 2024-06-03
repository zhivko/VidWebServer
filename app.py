
#https://flask.palletsprojects.com/en/3.0.x/installation/
# pip install -r requirements.txt
#flask run
#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
# test
# https://blog.miguelgrinberg.com/post/running-your-flask-application-over-https
from flask import current_app, Flask, redirect, render_template, request, send_from_directory
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
from shapely.geometry import LineString, Point
from shapely import set_precision
from shapely import distance
from threading import Thread, Lock

import math

import pytz

import numpy as np
import claudeTest
import yfinance as yahooFinance
import sys
from decimal import Decimal, getcontext

from matplotlib import image 
from matplotlib import pyplot as plt 


import pandas as pd
from datetime import timedelta
import time, threading
import json
import jsonpickle
from typing import List
import pybit

from datetime import datetime, timezone
from zoneinfo import ZoneInfo
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
#global lineCounter, dfs, interval, crteD

from MyFlask import MyFlask

from Init import initialCheckOfData
from threading import Thread
from sympy.physics.units.definitions.unit_definitions import seconds


app = MyFlask.app()

MyFlask.app().logger.info("starting ...")

from Util import read, write
from Init import calculateCrossSections, getDataPath, pullNewData, symbolsAndStocks, symbols, stocks

 
claudRecomendation = dict()
thread2 = None

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
# 1 3 5 15 30 60 120 240 360 720â€ƒminute
# Dâ€ƒday
# Wâ€ƒweek
# Mâ€ƒmonth
ws.kline_stream(
    interval='1',  # 5 minute, https://bybit-exchange.github.io/docs/v5/enum#interval
    symbol= mysymbol, # "BTCUSDT",
    callback=handle_message,
)
'''

def getCrtaWithIndex(index, symbol, crteD):
    i=0
    for crta in Crta.get_crteDforSymbol(symbol, crteD):
        if symbol in crta.symbol:
            if i==index:
                return crta
            i=i+1
    return None

def writeCrtaWithIndex(index, symbol, crta: Crta):
    crteD=read('crteD')
    i=0
    if symbol in crteD.keys():
        for crta1 in crteD[symbol]:
            if index==crta1.i:
                crta1 = crta
                #crteD[symbol][i] = crta
                break
            i=i+1
            
            
    for crta in crteD[symbol]:
        print(crta.plotlyLine());
            
    return None

def getNextIndex(symbol, crteD):
    ret=0
    if symbol in crteD.keys():
        if len(crteD[symbol])>0:
            for crta in crteD[symbol]:
                if ret < crta.i:
                    ret = crta.i
            ret = ret + 1
    return ret

def getPlotData(symbol, dfs, crteD):
    #df['time'] = df['timestamp'].apply(lambda x: str(x)[14:4])
    #f = lambda x: dt.datetime.utcfromtimestamp(int(x)/1000)
    #df['time'] = df['timestamp'].apply(f)
    #x = df['time'].apply(lambda x: int(x)).tolist()
    #x = df['timestamp'].index.astype("str").tolist()
    howmany = 1000
    if symbol in symbols:
        howmany = 1000
    
    
    x = dfs[symbol].tail(howmany).index.astype('str').tolist()
    open_ = dfs[symbol].tail(howmany)['open'].astype(float).tolist()
    high = dfs[symbol].tail(howmany)['high'].astype(float).tolist()
    low = dfs[symbol].tail(howmany)['low'].astype(float).tolist()
    close = dfs[symbol].tail(howmany)['close'].astype(float).tolist()
    volume = dfs[symbol].tail(howmany)['volume'].astype(float).tolist()
    
    ind1 = dfs[symbol].tail(howmany)['stoRsi'].astype(float).tolist()
    signal = dfs[symbol].tail(howmany)['stoSignal'].astype(float).tolist()

    lines = [];
    for crta in Crta.get_crteDforSymbol(symbol, crteD):
        lines.append(crta.plotlyLine());
            
    krogci_x, krogci_y, krogci_radius = calculateCrossSections(symbol, crteD)
    
    if symbol in symbols:
        dt1 = datetime.utcfromtimestamp(dfs[symbol].iloc[-1].timestamp) - timedelta(days=200)
    elif symbol in stocks:
        dt1 = datetime.utcfromtimestamp(dfs[symbol].iloc[-1].timestamp) - timedelta(days=400)
    
    dt2 = datetime.utcfromtimestamp(dfs[symbol].iloc[-1].timestamp) + timedelta(days=30)

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
    MyFlask.app().logger.error(str(error))
    MyFlask.app().logger.error(traceback.format_exc())
    
    
@app.route('/scroll', methods=['POST'])
def scroll():
    crteD=read('crteD')
    dt1 = datetime.now()
    dfs=read('dfs')
    dt2 = datetime.now()
    
    MyFlask().app().logger.info("loading took: " + str((dt2-dt1).total_seconds()) + "s.")
    
    
    symbol = request.args.get('pair')
    if symbol==None:
        symbol = "BTCUSDT"
        
    contentJson = request.json
    MyFlask.app().logger.info(contentJson)

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
    

    xaxis0_ = pd.to_datetime(xaxis0_)
    xaxis0_ = xaxis0_.floor('1s')
    xaxis1_ = pd.to_datetime(xaxis1_)
    xaxis1_ = xaxis1_.floor('1s')
    
    #xaxis0_ = xaxis0_.strftime('%Y-%m-%d %H:00:00')
    #xaxis1_ = xaxis1_.strftime('%Y-%m-%d %H:00:00')
    
    xaxis0_ = xaxis0_.replace(tzinfo=pytz.UTC)
    xaxis1_ = xaxis1_.replace(tzinfo=pytz.UTC)
    
    df_range = dfs[symbol].loc[pd.Timestamp(xaxis0_):pd.Timestamp(xaxis1_)]
    
    x = df_range.index.astype("str").tolist()
    open_ = df_range['open'].astype(float).tolist()
    high = df_range['high'].astype(float).tolist()
    low = df_range['low'].astype(float).tolist()
    close = df_range['close'].astype(float).tolist()
    volume = df_range['volume'].astype(float).tolist()
    lines = [];
    for crta in Crta.get_crteDforSymbol(symbol, crteD):
        lines.append(crta.plotlyLine());
    
    krogci_x, krogci_y, krogci_radius = calculateCrossSections(symbol, crteD)
    
    return {'x_axis': x, 'open': open_, 'high': high, 'low': low, 'close': close, 'volume': volume,'lines': lines, 'title': symbol, 
            'krogci_x': krogci_x, 'krogci_y': krogci_y, 'krogci_radius': krogci_radius,
           }, 200
    

@app.route('/deleteLine', methods=['POST'])
def deleteLine():
    crteD=read('crteD')
    dfs=read('dfs')
    crta: Crta
    
    symbol = request.args.get('pair')
    if symbol==None:
        symbol = "BTCUSDT"
            
    line_name = request.args.get('name')
    MyFlask.app().logger.info("Delete line for symbol: " + symbol + " with name: " + line_name)
    
    crta = crteD[line_name]
    crta.removeFromcrteD()

    MyFlask.app().logger.info("Delete line for symbol: "+symbol+" ...Done.")
    return getPlotData(symbol, dfs, crteD), 200

@app.route('/addLine', methods=['POST'])
def addLine():
    '''
    remote_ip = request.headers.get('X-Forwarded-For')
    if remote_ip != '89.233.122.140':
        return "forbidden", 403
    '''
    crteD = read('crteD')
    dfs = read('dfs')
    symbol = request.args.get('pair')
    if symbol==None:
        symbol = "BTCUSDT"
    
    MyFlask.app().logger.info("/addLine for symbol: " + symbol)
            
    contentJson = request.json
    MyFlask.app().logger.info(contentJson)

    crtePath = getDataPath(symbol) + os.sep + "crte.data"
    
    if 'type' in contentJson.keys() and contentJson['type']=='line':
        crta=Crta(getNextIndex(symbol, crteD), contentJson['x0'], contentJson['y0'], contentJson['x1'], contentJson['y1'], symbol)
        crta.writeCrteD(crteD)
        return getPlotData(symbol, dfs, crteD), 200
    elif list(contentJson.keys())[0].startswith("shapes"):
        MyFlask.app().logger.info("Correcting one line...")
        x = re.search(r"shapes\[(.*)\].*", list(contentJson.keys())[0])
        strI = x.group(1)
        intI=int(strI)
        crta = getCrtaWithIndex(intI, symbol, crteD)

        MyFlask.app().logger.info("Correcting one line " + crta.ime + " strI: " + str(intI))
        if not crta is None:
            if 'shapes['+strI+'].x0' in list(contentJson.keys()):
                crta.changeX0(contentJson['shapes['+strI+'].x0'])
            if 'shapes['+strI+'].y0' in list(contentJson.keys()):
                crta.y0 = contentJson['shapes['+strI+'].y0']
            if 'shapes['+strI+'].x1' in list(contentJson.keys()):
                crta.changeX1(contentJson['shapes['+strI+'].x1'])
            if 'shapes['+strI+'].y1' in list(contentJson.keys()):
                crta.y1 = contentJson['shapes['+strI+'].y1']
            crta.writeCrteD(crteD)
            return getPlotData(symbol, dfs, crteD), 200
        else:
            MyFlask.app().logger.warn("Did not find crta: " + str(intI))
    else:
        MyFlask.app().logger.warn("Unknown json: " + contentJson)

    MyFlask.app().logger.info("/addLine for symbol: " + symbol + "... Done.")
    return "ok", 200

'''
@app.route('/favicon.ico')
def favicon():
    print(os.path.join(MyFlask.app().root_path, 'static'))
    return send_from_directory(MyFlask.app().static_folder, 'favicon.ico') 
 
'''    

'''
@app.errorhandler(404)
def page_not_found(error):
    return render_template('./404.html'), 404
'''

def threaded_function2(symbol, start):
    global thread2
    dfs=read('dfs')
    pullNewData(symbol, start, dfs)
    thread2 = None



@app.route('/',methods = ['GET'])
def root():
    return redirect("/index.html", code=302)
    #return render_template('./404.html'), 404

@app.route('/index.html')
def index():
    dt1 = datetime.now()
    dfs=read('dfs')
    crteD=read('crteD')
    dt2 = datetime.now()
    
    MyFlask().app().logger.info("loading took: " + str((dt2-dt1).total_seconds()) + "s.")


    global thread2
    
    
    
    symbol = request.args.get('pair')
    if(symbol == None or symbol==""):
        symbol = "BTCUSDT"
    
    mydata = getDataPath(symbol) + os.sep + symbol + ".data"
    if not os.path.isfile(mydata):
        start = int(datetime(2009, 1, 1).timestamp()* 1000)
        if thread2!=None and thread2.is_alive():
            return "Thread for collecting data is running... Try later..."
        else:
            thread2 = Thread(target = threaded_function2, args = (symbol, start))
            thread2.start()
            return "Thread for collecting data has been started... Try later..."
    '''   
    else:
        if not symbol in dfs.keys():
            dfs[symbol] = pd.read_csv(mydata)
            dfs[symbol] = dfs[symbol].drop(['timestamp'], axis=1)
            dfs[symbol] = dfs[symbol].rename(columns={"timestamp.1": "timestamp"})
            f = lambda x: datetime.utcfromtimestamp(int(x)/1000)
            dfs[symbol].index = dfs[symbol].timestamp.apply(f)
    '''
    
    #MyFlask.app().logger.info(dfs[symbol])
    plot_data1 = getPlotData(symbol, dfs, crteD)
    
    tickers_data = " "
    for symb in symbolsAndStocks:
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
    return send_from_directory(os.path.join(MyFlask.app().root_path, 'static'),
                               'favicon.ico', mimetype='image/vnd.microsoft.icon')

if __name__ == '__main__':
    MyFlask.app().logger.info("Start threadInitialCheck")    
    threadInitialCheck = Thread(target = initialCheckOfData, args = ())
    threadInitialCheck.start()
    MyFlask.app().run(host = '127.0.0.1', port = '8000', debug=True, threaded=False)
