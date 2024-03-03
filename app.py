#https://flask.palletsprojects.com/en/3.0.x/installation/
#pip install -r requirements.txt
#flask run
#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
# test
# https://blog.miguelgrinberg.com/post/running-your-flask-application-over-https
from flask import Flask, render_template, request, send_from_directory
from flask_debug import Debug
import os.path
import traceback
import sys
from Crta import Crta
import re
from intersect import line_intersection, crosses
import logging
import locale


from pybit.unified_trading import HTTP
from pybit.unified_trading import WebSocket

import pandas as pd
import datetime as dt
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
global lineCounter, df, interval, krogci_x, krogci_y


lineCounter=0
krogci_x=[]
krogci_y=[]
mysymbol = "BTCUSDT"
interval = 60
locale.setlocale(locale.LC_ALL, 'sl_SI')

app = Flask(__name__,
            static_folder='./static',
            template_folder='./templates')


jsonpickle.set_encoder_options('json', sort_keys=True, indent=4)

#crte = Crta[]
crtePath = "crte.data"
crte: List[Crta] = []
print (os.path.abspath("crte.data"))
if os.path.isfile(crtePath):
    with open(crtePath, 'r') as f:
        json_str = f.read()
        crte = jsonpickle.decode(json_str)


with open("./authcreds.json") as j:
    creds = json.load(j)

kljuc = creds['kljuc']
geslo = creds['geslo']



def gmail(message):
    global creds, mysymbol
    gmailEmail = creds['gmailEmail']
    gmailPwd = creds['gmailPwd']


    try:
        server = smtplib.SMTP('smtp.gmail.com', 587)
        server.ehlo()
        server.starttls()
        server.login(gmailEmail,gmailPwd)
        #server.set_debuglevel(1)
        
        message["Subject"] = mysymbol
        message["From"] = gmailEmail
        
        message["To"] = creds['emailTo'] #', '.join(["vid.zivkovic@gmail.com", "klemen.zivkovic@gmail.com"])
        
        server.send_message(message)
        server.close()
        app.logger.info('successfully sent the mail')
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



session = HTTP(api_key=kljuc, api_secret=geslo, testnet=False)


result = session.get_tickers(category="linear").get('result')['list']

tickers = [asset['symbol'] for asset in result if asset['symbol'].endswith('USDT')]
app.logger.info(tickers)

def calculateCrossSections():
    global krogci_x, krogci_y, mysymbol
    krogci_x=[]
    krogci_y=[]
    text_data = ''
    for index, row in df.tail(100).iterrows():
        loc = df.index.get_loc(row.name)
        line1 = (
                (df.iloc[loc].timestamp, df.iloc[loc].close),
                (df.iloc[loc-1].timestamp, df.iloc[loc-1].close),
                )
        for crta in crte:
            line2 = (
                    (crta.x0_timestamp, crta.y0),
                    (crta.x1_timestamp, crta.y1)
                    )
            aliCrosses = crosses(line1,line2)
            if aliCrosses:
                inter = line_intersection(line1,line2)
                time = dt.datetime.utcfromtimestamp(int(inter[0])/1000).strftime("%Y-%m-%d %H:%M:%S")
                krogci_x.append(time)
                krogci_y.append(inter[1])
                
                if text_data=='':
                    text_data = "data from https://crypto.zhivko.eu\n"
                
                text_data = text_data + \
                        'time:  ' + time + '\n' + \
                        'price: ' + '{:0,.2f}'.format(inter[1]) + ' $USD/BTC\n\n'
                      
            
    if text_data!='':
        text =  'Crossing happened for ' + mysymbol + '\n' + text_data
        message = MIMEMultipart("alternative")
        part1 = MIMEText(text, "plain")
        message.attach(part1)
        gmail(message)
        

def pullNewData(mysymbol, start, interval):
    global df
    added = False
    while True:
        app.logger.info(dt.datetime.now(pytz.timezone('Europe/Ljubljana')).strftime("%d.%m.%Y %H:%M:%S") + \
            ' Collecting data from ' + \
            dt.datetime.fromtimestamp(start/1000).strftime("%d.%m.%Y %H:%M:%S"))

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
        added=True
        app.logger.info("Appended data.")
        if len(latest) == 1:
            break
    
    if added:
        df.drop_duplicates(subset=['timestamp'], keep='last', inplace=True)
        df.to_csv(dataPath)
        app.logger.info("Saved to csv.")
        
        calculateCrossSections()


def get_last_timestamp(df):
    return int(df.timestamp[-1:].values[0])

dataPath = mysymbol + '.data'
if not os.path.isfile(dataPath):
    start = int(dt.datetime(2009, 1, 1).timestamp()* 1000)
    df = pd.DataFrame()
        
    pullNewData(mysymbol, start, interval)

else:
    df=pd.read_csv(dataPath)
    df = df.drop(['timestamp'], axis=1)
    df = df.rename(columns={"timestamp.1": "timestamp"})
    f = lambda x: dt.datetime.utcfromtimestamp(int(x)/1000)
    df.index = df.timestamp.apply(f)

app.logger.info(df)



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
    global currentHour
    if dt.datetime.now().hour != currentHour:
        currentHour = dt.datetime.now().hour
        app.logger.info("beep - hour changed: " + str(currentHour))    
        start = get_last_timestamp(df)
        pullNewData(mysymbol, start, interval)
    
    threading.Timer(5, repeatPullNewData).start()
    
repeatPullNewData()





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
    howmany = 1000
    x = df.tail(howmany).index.astype("str").tolist()
    open_ = df.tail(howmany)['open'].astype(float).tolist()
    high = df.tail(howmany)['high'].astype(float).tolist()
    low = df.tail(howmany)['low'].astype(float).tolist()
    close = df.tail(howmany)['close'].astype(float).tolist()
    volume = df.tail(howmany)['volume'].astype(float).tolist()
    lines = [];
    for crta in crte:
        lines.append(crta.plotlyLine());
    return {'x_axis': x, 'open': open_, 'high': high, 'low': low, 'close': close, 'volume': volume,'lines': lines, 'title': mysymbol, 'krogci_x': krogci_x, 'krogci_y': krogci_y}
    

@app.errorhandler(Exception)
def all_exception_handler(error):
    print(str(error))
    

@app.route('/scroll', methods=['POST'])
def scroll():
    contentJson = request.json
    app.logger.info(contentJson)
    

    df_range = df.loc[pd.Timestamp(contentJson['xaxis.range[0]']):pd.Timestamp(contentJson['xaxis.range[1]'])]
    
    x = df_range.index.astype("str").tolist()
    open_ = df_range['open'].astype(float).tolist()
    high = df_range['high'].astype(float).tolist()
    low = df_range['low'].astype(float).tolist()
    close = df_range['close'].astype(float).tolist()
    volume = df_range['volume'].astype(float).tolist()
    lines = [];
    for crta in crte:
        lines.append(crta.plotlyLine());
    
    return {'x_axis': x, 'open': open_, 'high': high, 'low': low, 'close': close, 'volume': volume,'lines': lines, 'title': mysymbol, 'krogci_x': krogci_x, 'krogci_y': krogci_y}, 200
    

@app.route('/deleteLine', methods=['POST'])
def deleteLine():
    line_no = request.args.get('line_no')
    needsWrite=False
    for crta in crte:
        if crta.i == int(line_no):
            needsWrite=True
            crte.remove(crta);

    if needsWrite:
        with open(crtePath,'w') as f:
            strJson = jsonpickle.encode(crte, indent=2)
            f.write(strJson)    
    
    return "ok", 200

@app.route('/addLine', methods=['POST'])
def addLine():
    contentJson = request.json
    app.logger.info(contentJson)

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
            calculateCrossSections()
        else:
            app.logger.info("Did not find crta: " + intI)
    else:
        app.logger.info(contentJson)


    if needsWrite:
        try:
            with open(crtePath,'w') as f:
                strJson = jsonpickle.encode(crte, indent=2)
                f.write(strJson)
                 
        except:
            if os.path.isfile(crtePath):        
                os.remove(crtePath)
            app.logger.error(traceback.format_exc())
            # or
            app.logger.info(sys.exc_info()[2])           

    
    return "ok", 200

'''
@app.route('/favicon.ico')
def favicon():
    print(os.path.join(app.root_path, 'static'))
    return send_from_directory(app.static_folder, 'favicon.ico') 
'''    


@app.route('/')
def home():
    plot_data1 = get_plot_data()
    return render_template('./index.html', plot_data=plot_data1)
    #return render_template_string(template,plot_data=plot_data1)


#Debug(app)
#app = Flask(__name__)
#app.config['DEBUG'] = True

if __name__ != '__main__':
    gunicorn_logger = logging.getLogger('gunicorn.error')
    app.logger.handlers = gunicorn_logger.handlers
    app.logger.setLevel(gunicorn_logger.level)

if __name__ == '__main__':
    app.run(host = '127.0.0.1', port = '8000', debug=True)
    


