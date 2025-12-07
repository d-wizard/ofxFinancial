import os
import json
import argparse
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

# Main start
if __name__== "__main__":
    history = {}
    getStockHistory("AAPL", "2025-11-01", "2025-12-01", history)
    getStockHistory("MSFT", "2025-10-01", "2025-12-01", history)
    history = sorted(history.items())
    print(history)

    plotStockHistory("MSFT", "2020-10-01", "2025-12-01")
