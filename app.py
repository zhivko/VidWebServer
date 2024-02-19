#https://flask.palletsprojects.com/en/3.0.x/installation/
#pip install -r requirements.txt
#flask run
#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
# test
from flask import Flask, render_template, render_template_string, request
from flask_debug import Debug
import os.path
import traceback
import sys
from Crta import Crta
import re

from pybit.unified_trading import HTTP
from pybit.unified_trading import WebSocket

import pandas as pd
import datetime as dt
import time 
import json
import jsonpickle
from typing import List
import pybit

from datetime import datetime, timezone, tzinfo
import pytz

global lineCounter

lineCounter=0

jsonpickle.set_encoder_options('json', sort_keys=True, indent=4)

#crte = Crta[]
crtePath = "crte.data"
crte: List[Crta] = []
print (os.path.abspath("crte.data"))
if os.path.isfile(crtePath):
    with open(crtePath, 'r') as f:
        json_str = f.read()
        crte = jsonpickle.decode(json_str)





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



with open("./authcreds.json") as j:
    creds = json.load(j)

kljuc = creds['kljuc']
geslo = creds['geslo']
  
session = HTTP(api_key=kljuc, api_secret=geslo, testnet=False)


result = session.get_tickers(category="linear").get('result')['list']

tickers = [asset['symbol'] for asset in result if asset['symbol'].endswith('USDT')]
print(tickers)

mysymbol = "BTCUSDT"




def get_last_timestamp(df):
    return int(df.timestamp[-1:].values[0])

dataPath = mysymbol + '.data'
if not os.path.isfile(dataPath):
    start = int(dt.datetime(2024, 1, 1).timestamp()* 1000)
    interval = 60
    df = pd.DataFrame()
    
    while True:
        response = session.get_kline(category='linear', 
                                     symbol=mysymbol, 
                                     start=start,
                                     interval=interval).get('result')
        
        latest = format_data(response)
        
        if not isinstance(latest, pd.DataFrame):
            break
        
        start = get_last_timestamp(latest)
        
        time.sleep(0.1)
        
        df = pd.concat([df, latest])
        print(f'Collecting data starting {dt.datetime.fromtimestamp(start/1000)}')
        if len(latest) == 1: break
    
    
    df.drop_duplicates(subset=['timestamp'], keep='last', inplace=True)
    df.to_csv(dataPath)

else:
    df=pd.read_csv(dataPath)
    df.index = df.timestamp
    df = df.drop(['timestamp'], axis=1)
    df = df.rename(columns={"timestamp.1": "timestamp"})

print(df)



#response = session.get_kline(category='linear', 
#                             symbol=mysymbol, 
#                             interval='D').get('result')
#df = format_data(response)
# https://bybit-exchange.github.io/docs/v5/websocket/public/kline
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






def getCrtaWithIndex(index, crte: List[Crta]):
    for crta in crte:
        if crta.i==index:
            return crta


def get_plot_data():
    #df['time'] = df['timestamp'].apply(lambda x: str(x)[14:4])
    #f = lambda x: dt.datetime.utcfromtimestamp(int(x)/1000)
    #df['time'] = df['timestamp'].apply(f)
    #x = df['time'].apply(lambda x: int(x)).tolist()
    #x = df['timestamp'].index.astype("str").tolist()
    x = df.index.astype("str").tolist()
    y = df['close'].astype(float).tolist()
    volume = df['volume'].astype(float).tolist()
    lines = [];
    for crta in crte:
        lines.append(crta.plotlyLine());
    return {'x_axis': x, 'y_axis': y, 'volume': volume,'lines': lines, 'title': mysymbol}
    
app = Flask(__name__)


@app.route('/addLine', methods=['POST'])
def addLine():
    contentJson = request.json
    print(contentJson)

    needsWrite=False
    
    if 'type' in contentJson.keys() and contentJson['type']=='line':
        crta1=Crta(len(crte), contentJson['x0'], contentJson['y0'], contentJson['x1'], contentJson['y1'])
        crte.append(crta1)
        needsWrite=True
    elif list(contentJson.keys())[0].startswith("shapes"):
        x = re.search(r"shapes\[(.*)\].*", list(contentJson.keys())[0])
        strI = x.group(1)
        intI=int(strI)
        crta = getCrtaWithIndex(intI, crte)
        if not crta is None:
            if 'shapes['+strI+'].x0' in list(contentJson.keys()):
                crta.x0 = contentJson['shapes['+strI+'].x0']
            if 'shapes['+strI+'].y0' in list(contentJson.keys()):
                crta.y0 = contentJson['shapes['+strI+'].y0']
            if 'shapes['+strI+'].x1' in list(contentJson.keys()):
                crta.x1 = contentJson['shapes['+strI+'].x1']
            if 'shapes['+strI+'].y1' in list(contentJson.keys()):
                crta.y1 = contentJson['shapes['+strI+'].y1']
            needsWrite=True
        else:
            print("Did not find crta: " + intI)
    else:
        print(contentJson)


    if needsWrite:
        try:
            with open(crtePath,'w') as f:
                strJson = jsonpickle.encode(crte, indent=2)
                f.write(strJson)
                 
        except:
            if os.path.isfile(crtePath):        
                os.remove(crtePath)
            exc = sys.exc_info()
            print(traceback.format_exc())
            # or
            print(sys.exc_info()[2])           

    
    return "ok", 200

@app.route('/')
def home():
    plot_data1 = get_plot_data()
    return render_template('./index.html', plot_data=plot_data1)
    #return render_template_string(template,plot_data=plot_data1)



#Debug(app)
app.run(debug=True) #, ssl_context='adhoc')


