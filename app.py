#https://flask.palletsprojects.com/en/3.0.x/installation/
#pip install -r requirements.txt
#flask run
#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
# test
# https://blog.miguelgrinberg.com/post/running-your-flask-application-over-https
from flask import Flask, redirect, render_template, request, send_from_directory
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
import numpy as np

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
#from pandas.conftest import datapath
global lineCounter, dfs, interval, crteD

crteD = dict()
dfs = dict()

app = Flask(__name__,
            static_folder='./static',
            template_folder='./templates')

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


symbols = {'BTCUSDT', 'ETHUSDT', 'SOLUSDT'}

lineCounter=0
dfs={}
interval = 60
locale.setlocale(locale.LC_ALL, 'sl_SI')

jsonpickle.set_encoder_options('json', sort_keys=True, indent=4)

#crte = Crta[]

with open("./authcreds.json") as j:
    creds = json.load(j)

kljuc = creds['kljuc']
geslo = creds['geslo']



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
    
    if not data:
        return 
    
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
    #return data
    f = lambda x: dt.datetime.utcfromtimestamp(int(x)/1000)
    data.index = data.timestamp.apply(f)
    return data[::-1].apply(pd.to_numeric)

def getDataPath(symbol):
        path = pathlib.Path("." + os.sep + symbol).resolve()
        if not (os.path.isdir(path)):
            os.mkdir(path, mode = 0o777)
            app.logger.info("Directory '% s' created" % path)
        return os.path.realpath(path);

session = HTTP(api_key=kljuc, api_secret=geslo, testnet=False)
result = session.get_tickers(category="linear").get('result')['list']
tickers = [asset['symbol'] for asset in result if (asset['symbol'].endswith('USDT') or asset['symbol'].endswith('BTC'))]
app.logger.info(tickers)
tickers_data=""
for symbol in symbols:
    crtePath = getDataPath(symbol) + os.sep + "crte.data"
    app.logger.info(crtePath)
    if os.path.isfile(crtePath):
        with open(crtePath, 'r') as f:
            json_str = f.read()
            crte = jsonpickle.decode(json_str)
            crteD[symbol] = crte
    else:
        crte: List[Crta] = []
        crteD[symbol] = crte

def sendMailForLastCrossSections(symbol, krogci_x, krogci_y):
    i=0;
    text_data='';
    for x in krogci_x:
        text_data = text_data + \
                'time:  ' + krogci_x[i] + '\n' + \
                'price: ' + '{:0,.2f}'.format(krogci_y[i]) + ' $USD/BTC\n\n'
        i=i+1;
                      
            
    if text_data!='':
        text = 'https://crypto.zhivko.eu\n';
        text = text + 'Crossing happened for ' + symbol + '\n'
        text = text + text_data
        message = MIMEMultipart("alternative")
        part1 = MIMEText(text, "plain")
        message.attach(part1)
        gmail(message, symbol)

def calculateCrossSections(symbol):
    krogci_x=[]
    krogci_y=[]
    for index, row in dfs[symbol].tail(100).iterrows():
        loc = dfs[symbol].index.get_loc(row.name)
        first_line = LineString([Point(dfs[symbol].iloc[loc].timestamp, dfs[symbol].iloc[loc].low), Point(dfs[symbol].iloc[loc].timestamp, dfs[symbol].iloc[loc].high)])
        for crta in crteD[symbol]:
            second_line = LineString([Point(crta.x0_timestamp, crta.y0),Point(crta.x1_timestamp, crta.y1)])
            if first_line.intersects(second_line):
                intersection = first_line.intersection(second_line)
                time = dt.datetime.utcfromtimestamp(int(intersection.coords[0][0])/1000).strftime("%Y-%m-%d %H:%M:%S")
                krogci_x.append(time)
                krogci_y.append(intersection.coords[0][1])
    return krogci_x, krogci_y


def pullNewData(symbol, start, interval):
    global dfs
    added = False
    
    dataPath = getDataPath(symbol) + os.sep + symbol + '.data'
    
    while True:
        app.logger.info(dt.datetime.now(pytz.timezone('Europe/Ljubljana')).strftime("%d.%m.%Y %H:%M:%S") + \
            ' Collecting data for: ' + symbol + ' from ' + \
            dt.datetime.fromtimestamp(start/1000).strftime("%d.%m.%Y %H:%M:%S"))

        response = session.get_kline(category='linear', 
                                     symbol=symbol, 
                                     start=start,
                                     interval=interval).get('result')
        
        latest = format_data(response)
        
        if not isinstance(latest, pd.DataFrame):
            break
        
        start = latest.timestamp[-1:].values[0]
        
        time.sleep(0.1)
        
        if not symbol in dfs.keys():
            dfs[symbol] = latest
        else:
            dfs[symbol] = pd.concat([dfs[symbol], latest])
        
        added=True
        app.logger.info("Appended data.")
        if len(latest) == 1:
            break
    
    if added:
        dfs.get(symbol).drop_duplicates(subset=['timestamp'], keep='last', inplace=True)
        dfs.get(symbol).to_csv(dataPath)
        
        app.logger.info("Saved to csv.")


def get_last_timestamp(symbol):
    if not symbol in dfs.keys():
        return int(dt.datetime(2009, 1, 1).timestamp()* 1000)

    return int(dfs.get(symbol).timestamp[-1:].values[0])



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

currentHour = 0
def repeatPullNewData():
    global currentHour, symbols
    if dt.datetime.now().hour != currentHour:
        currentHour = dt.datetime.now().hour
        app.logger.info("beep - hour changed: " + str(currentHour))
        for symbol in symbols:
            dataPath = getDataPath(symbol) + os.sep + symbol + '.data'            
            if not symbol in dfs.keys():
                if os.path.isfile(dataPath):
                    dfs[symbol] = pd.read_csv(dataPath)
                    dfs[symbol] = dfs[symbol].drop(['timestamp'], axis=1)
                    dfs[symbol] = dfs[symbol].rename(columns={"timestamp.1": "timestamp"})
                    f = lambda x: dt.datetime.utcfromtimestamp(int(x)/1000)
                    dfs[symbol].index = dfs[symbol].timestamp.apply(f)            
            
            start = int(dt.datetime(2009, 1, 1).timestamp()* 1000)
            if symbol in dfs.keys():
                start = get_last_timestamp(symbol)
            pullNewData(symbol, start, interval)
            
            krogci_x, krogci_y = calculateCrossSections(symbol)
            sendMailForLastCrossSections(symbol, krogci_x, krogci_y)

    
    threading.Timer(5, repeatPullNewData).start()
    
# function to create threads
def threaded_function(arg):
    repeatPullNewData()
 
 
if __name__ == "__main__":
    thread = Thread(target = threaded_function, args = ())
    thread.start()
    thread.join()
    print("thread finished...exiting")
    


def getCrtaWithIndex(index, symbol):
    i=0
    for crta in crteD[symbol]:
        if i==index:
            return crta
        i=i+1


def getPlotData(symbol):
    global crteD
    #df['time'] = df['timestamp'].apply(lambda x: str(x)[14:4])
    #f = lambda x: dt.datetime.utcfromtimestamp(int(x)/1000)
    #df['time'] = df['timestamp'].apply(f)
    #x = df['time'].apply(lambda x: int(x)).tolist()
    #x = df['timestamp'].index.astype("str").tolist()
    howmany = 1000
    x = dfs[symbol].tail(howmany).index.astype("str").tolist()
    open_ = dfs[symbol].tail(howmany)['open'].astype(float).tolist()
    high = dfs[symbol].tail(howmany)['high'].astype(float).tolist()
    low = dfs[symbol].tail(howmany)['low'].astype(float).tolist()
    close = dfs[symbol].tail(howmany)['close'].astype(float).tolist()
    volume = dfs[symbol].tail(howmany)['volume'].astype(float).tolist()
    lines = [];
    for crta in crteD[symbol]:
        lines.append(crta.plotlyLine());
    
    krogci_x, krogci_y = calculateCrossSections(symbol)
    return {'x_axis': x, 'open': open_, 'high': high, 'low': low, 'close': close, 'volume': volume,'lines': lines, 
            'title': symbol, 'krogci_x': krogci_x, 'krogci_y': krogci_y,
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
    

    df_range = dfs[symbol].loc[pd.Timestamp(contentJson['xaxis.range[0]']):pd.Timestamp(contentJson['xaxis.range[1]'])]
    
    x = df_range.index.astype("str").tolist()
    open_ = df_range['open'].astype(float).tolist()
    high = df_range['high'].astype(float).tolist()
    low = df_range['low'].astype(float).tolist()
    close = df_range['close'].astype(float).tolist()
    volume = df_range['volume'].astype(float).tolist()
    lines = [];
    for crta in crteD[symbol]:
        lines.append(crta.plotlyLine());
    
    krogci_x, krogci_y = calculateCrossSections(symbol)
    
    return {'x_axis': x, 'open': open_, 'high': high, 'low': low, 'close': close, 'volume': volume,'lines': lines, 'title': symbol, 'krogci_x': krogci_x, 'krogci_y': krogci_y}, 200
    

@app.route('/deleteLine', methods=['POST'])
def deleteLine():
    symbol = request.args.get('pair')
    if symbol==None:
        symbol = "BTCUSDT"
            
    line_name = request.args.get('name')
    needsWrite=False
    for crta in crteD[symbol]:
        if crta.ime == line_name:
            needsWrite=True
            crteD[symbol].remove(crta);

    crtePath = getDataPath(symbol) + os.sep + "crte.data"

    if needsWrite:
        calculateCrossSections();
        with open(crtePath,'w') as f:
            strJson = jsonpickle.encode(crteD[symbol], indent=2)
            f.write(strJson)    
    
    return "ok", 200

def writeCrte(symbol):
    crtePath = getDataPath(symbol) + os.sep + "crte.data"
    try:
        with open(crtePath,'w') as f:
            strJson = jsonpickle.encode(crteD[symbol], indent=2)
            f.write(strJson)
             
    except:
        if os.path.isfile(crtePath):        
            os.remove(crtePath)
        app.logger.error(traceback.format_exc())
        # or
        app.logger.info(sys.exc_info()[2])      


@app.route('/addLine', methods=['POST'])
def addLine():
    global crteD
    symbol = request.args.get('pair')
    if symbol==None:
        symbol = "BTCUSDT"
            
    contentJson = request.json
    app.logger.info(contentJson)

    crtePath = getDataPath(symbol) + os.sep + "crte.data"
    
    if 'type' in contentJson.keys() and contentJson['type']=='line':
        crta1=Crta(len(crte), contentJson['x0'], contentJson['y0'], contentJson['x1'], contentJson['y1'])
        
        crteD[symbol].append(crta1)
        writeCrte(symbol)
        calculateCrossSections(symbol)
    elif list(contentJson.keys())[0].startswith("shapes"):
        x = re.search(r"shapes\[(.*)\].*", list(contentJson.keys())[0])
        strI = x.group(1)
        intI=int(strI)
        crta = getCrtaWithIndex(intI, crteD[symbol])
        if not crta is None:
            if 'shapes['+strI+'].x0' in list(contentJson.keys()):
                crta.x0 = contentJson['shapes['+strI+'].x0']
            if 'shapes['+strI+'].y0' in list(contentJson.keys()):
                crta.y0 = contentJson['shapes['+strI+'].y0']
            if 'shapes['+strI+'].x1' in list(contentJson.keys()):
                crta.x1 = contentJson['shapes['+strI+'].x1']
            if 'shapes['+strI+'].y1' in list(contentJson.keys()):
                crta.y1 = contentJson['shapes['+strI+'].y1']
            writeCrte()
            calculateCrossSections(symbol)
            return getPlotData(), 200
        else:
            app.logger.info("Did not find crta: " + intI)
    else:
        app.logger.info(contentJson)

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


@app.route('/')
def home():
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
        dfs[symbol]=pd.read_csv(mydata)
        dfs[symbol] = dfs[symbol].drop(['timestamp'], axis=1)
        dfs[symbol] = dfs[symbol].rename(columns={"timestamp.1": "timestamp"})
        f = lambda x: dt.datetime.utcfromtimestamp(int(x)/1000)
        dfs[symbol].index = dfs[symbol].timestamp.apply(f)
    
    app.logger.info(dfs[symbol])
    plot_data1 = getPlotData(symbol)
    
    tickers_data = ""
    for symb in symbols:
        tickers_data = tickers_data + '<option value="'+symb+'">'+symb+'</option>'    
    
    return render_template('./index.html', plot_data=plot_data1, webpage_data={'tickers_data': tickers_data, 'selectedPair': symbol})
    #return render_template_string(template,plot_data=plot_data1)


#Debug(app)
#app = Flask(__name__)
#app.config['DEBUG'] = True

if __name__ == '__main__':
    app.run(host = '127.0.0.1', port = '8000', debug=True)
    


