#https://flask.palletsprojects.com/en/3.0.x/installation/
#pip install -r requirements.txt
#flask run
#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
from flask import Flask, render_template, render_template_string
from flask_debug import Debug

from pybit.unified_trading import HTTP
import pandas as pd
import datetime as dt
import time 
import json


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



with open("c:/work/klemen/authcreds.json") as j:
    creds = json.load(j)

key = creds['key']
secret = creds['secret']
  
session = HTTP(api_key=key, api_secret=secret, testnet=False)


result = session.get_tickers(category="linear").get('result')['list']

tickers = [asset['symbol'] for asset in result if asset['symbol'].endswith('USDT')]
print(tickers)

mysymbol = "BTCUSDT"




def get_last_timestamp(df):
    return int(df.timestamp[-1:].values[0])

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
f = lambda x: dt.datetime.utcfromtimestamp(int(x)/1000)
df.index = df.timestamp.apply(f)
df = df[::-1].apply(pd.to_numeric)



#response = session.get_kline(category='linear', 
#                             symbol=mysymbol, 
#                             interval='D').get('result')
#df = format_data(response)

print(df)




def get_plot_data():
    #df['time'] = df['timestamp'].apply(lambda x: str(x)[14:4])
    #f = lambda x: dt.datetime.utcfromtimestamp(int(x)/1000)
    #df['time'] = df['timestamp'].apply(f)
    #x = df['time'].apply(lambda x: int(x)).tolist()
    x = df['timestamp'].index.astype("str").tolist()
    y = df['close'].astype(float).tolist()
    return {'x_axis': x, 'y_axis': y, 'title': mysymbol}

app = Flask(__name__)

@app.route('/')
def home():
    plot_data1 = get_plot_data()
    return render_template('./index.html', plot_data=plot_data1)
    #return render_template_string(template,plot_data=plot_data1)




Debug(app)
app.run(debug=True)