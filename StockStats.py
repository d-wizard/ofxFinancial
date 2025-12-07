import os
import json
import argparse
from datetime import datetime
import yfinance as yf
import matplotlib.pyplot as plt

def plotStockHistory(ticker: str, start: str, end: str):
    """
    Plot historical stock prices for a given ticker symbol and date range.

    Parameters
    ----------
    ticker : str
        Stock ticker symbol (e.g., "AAPL", "MSFT")
    start : str
        Start date in "YYYY-MM-DD" format
    end : str
        End date in "YYYY-MM-DD" format
    """
    # Download price data
    data = yf.download(ticker, start=start, end=end)

    if data.empty:
        print("No data found. Check ticker or date range.")
        return
    
    # Plot closing prices
    plt.figure(figsize=(12, 6))
    plt.plot(data.index, data['Close'], label="Close Price", color='blue')
    
    plt.title(f"{ticker} Stock Price ({start} to {end})")
    plt.xlabel("Date")
    plt.ylabel("Price (USD)")
    plt.grid(True, linestyle='--', alpha=0.5)
    plt.legend()
    
    plt.tight_layout()
    plt.show()

################################################################################

def getStockHistory(ticker: str, start: str, end: str, history: dict):
    """
    Parameters
    ----------
    ticker : str
        Stock ticker symbol (e.g., "AAPL", "MSFT")
    start : str
        Start date in "YYYY-MM-DD" format
    end : str
        End date in "YYYY-MM-DD" format
    """
    data = yf.download(ticker, start=start, end=end)

    timestamps = data.index.tolist()
    temp = data['Close'].values.tolist()
    closeVals = []
    for t in temp:
        closeVals += t

    for i in range(len(timestamps)):
        try:
            history[timestamps[i]][ticker] = closeVals[i]
        except:
            history[timestamps[i]] = {}
            history[timestamps[i]][ticker] = closeVals[i]

################################################################################

def getNewestStockHistoryDate(history: dict):
    newestDate = None
    for h in history:
        if newestDate == None:
            newestDate = h
        elif newestDate < h:
            newestDate = h
    return newestDate

################################################################################

def tradeToDate(trade):
    return datetime.strptime(trade['Date'], "%Y-%m-%d")

################################################################################

def determineOldestTradeTime(trades):
    oldestTradeTime = None
    for trade in trades:
        tradeTimeStamp = tradeToDate(trade)
        if oldestTradeTime == None:
            oldestTradeTime = tradeTimeStamp
        elif tradeTimeStamp < oldestTradeTime:
            oldestTradeTime = tradeTimeStamp
    return oldestTradeTime

################################################################################

def getSymbols(trades):
    symbols = []
    for trade in trades:
        if trade["Symbol"] not in symbols:
            symbols.append(trade["Symbol"])
    return symbols

################################################################################

# Main start
if __name__== "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument("-t", "--trades", required=True, help="Json that defines the trades that were made.")
    args = parser.parse_args()

    # Parse the documents that contain transactions.
    with open(args.trades, 'r') as f:
        trades = json.load(f)
        startTime = determineOldestTradeTime(trades)
        startTimeStr = startTime.strftime("%Y-%m-%d")
        nowTimeStr = datetime.now().strftime("%Y-%m-%d")
        symbols = getSymbols(trades)

        history = {}
        for symbol in symbols:
            getStockHistory(symbol, startTimeStr, nowTimeStr, history)

        print(history[getNewestStockHistoryDate(history)])

