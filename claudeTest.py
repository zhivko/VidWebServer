import numpy as np
import talib
from pybit.unified_trading import HTTP
import datetime
import json
import time


# Bybit API credentials
api_key = "YOUR_API_KEY"
api_secret = "YOUR_API_SECRET"

with open("./authcreds.json") as j:
    creds = json.load(j)

api_key = creds['kljuc']
api_secret = creds['geslo']



# Create a session with Bybit V5 API
session = HTTP(
    api_key=api_key,
    api_secret=api_secret
)

# Function to fetch historical price data from Bybit
def fetch_price_data(symbol, interval, limit):
    try:
        # Calculate the start time for the last 100 periods
        end_time = int(time.time() * 1000)
        start_time = int(datetime.datetime(2024, 3, 15).timestamp()* 1000 - (limit * 3600 * 1000))
        
        price_data = session.get_kline(
            category='linear',
            symbol=symbol,
            interval=interval,
            start=start_time,
            limit=limit
        )
        return price_data["result"]
    except Exception as e:
        raise Exception(f"Failed to fetch price data: {str(e)}")

# Function to calculate RSI
def calculate_rsi(close_prices, timeperiod=14):
    rsi = talib.RSI(np.array(close_prices), timeperiod)
    return rsi[-1]

# Function to calculate MACD
def calculate_macd(close_prices, fastperiod=12, slowperiod=26, signalperiod=9):
    macd, signal, _ = talib.MACD(np.array(close_prices), fastperiod, slowperiod, signalperiod)
    return macd[-1], signal[-1]

# Function to calculate Stochastic
def calculate_stochastic(high_prices, low_prices, close_prices, fastk_period=14, slowk_period=3, slowd_period=3):
    slowk, slowd = talib.STOCH(np.array(high_prices), np.array(low_prices), np.array(close_prices),
                               fastk_period, slowk_period, slowk_matype=0, slowd_period=slowd_period, slowd_matype=0)
    return slowk[-1], slowd[-1]

def getSuggestion(price_data):
    # Fetch historical price data
    # symbol = "BTCUSDT"
    #price_data = fetch_price_data(symbol, interval, limit)
    
    # Extract close, high, and low prices from the price data
    # start, open, high, low, close
    close_prices = price_data.iloc[::-1].loc[:,"close"]
    high_prices = price_data.iloc[::-1].loc[:,"high"]
    low_prices = price_data.iloc[::-1].loc[:,"low"]
    
    # Calculate indicators
    rsi = calculate_rsi(close_prices)
    macd, signal = calculate_macd(close_prices)
    slowk, slowd = calculate_stochastic(high_prices, low_prices, close_prices)
    
    # Generate buy/sell signals based on the combination of indicator values
    if rsi < 30 and macd > signal and slowk < 20 and slowd < 20:
        suggestion = "Buy"
    elif rsi > 70 and macd < signal and slowk > 80 and slowd > 80:
        suggestion = "Sell"
    else:
        suggestion = "Hold"
    
    # Print the current price and buy/sell suggestion
    current_price = close_prices[0]
    
    explanation = f"RSI: {rsi:.2f}<br>"
    explanation += f"MACD: {macd:.2f}<br>"
    explanation += f"MACD Signal: {signal:.2f}<br>"
    explanation += f"Stochastic %K: {slowk:.2f}<br>"
    explanation += f"Stochastic %D: {slowd:.2f}"
    
    return suggestion, explanation, current_price

'''
interval = "60"  # 1-hour interval
limit = 100  # Number of data points to fetch
price_data = fetch_price_data("BTCUSDT", interval, limit)
suggestion, explanation = getSuggestion(price_data)
print(suggestion)
print("Explanation:\n")
print(explanation)
'''