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

def includeSymbols(trades, symbolsToInclude):
    retVal = []
    for trade in trades:
        if trade["Symbol"] in symbolsToInclude:
            retVal.append(trade)
    return retVal

################################################################################

def excludeSymbols(trades, symbolsToExclude):
    retVal = []
    for trade in trades:
        if trade["Symbol"] not in symbolsToExclude:
            retVal.append(trade)
    return retVal

################################################################################

def getProfit(trades, stockHistory):
    nowStockValues = stockHistory[getNewestStockHistoryDate(stockHistory)]
    totalSpent = 0
    curValue = 0
    for trade in trades:
        tradeShares = float(trade["Shares"])
        tradeCostPer = float(trade["Cost"])
        tradeTotal = tradeShares * tradeCostPer
        nowValuePer = float(nowStockValues[trade["Symbol"]])
        nowValueTotal = tradeShares * nowValuePer

        totalSpent += tradeTotal
        curValue += nowValueTotal
    
    return [totalSpent, curValue]

################################################################################

def getProfitOverTime(trades, stockHistory):
    for trade in trades:
        tradeShares = float(trade["Shares"])
        tradeCostPer = float(trade["Cost"])
        tradeDate = tradeToDate(trade)
        tradeSymbol = trade["Symbol"]
        tradeTotal = tradeShares * tradeCostPer
        trade["History"] = []
        for stockDay in stockHistory:
            if stockDay >= tradeDate:
                dayValuePer = float(stockHistory[stockDay][tradeSymbol])
                dayValueTotal = tradeShares * dayValuePer
                dayProfit = dayValueTotal - tradeTotal

                value = {}
                value["Value"] = dayValueTotal
                value["Profit"] = dayProfit
                value["Date"] = stockDay
                trade["History"].append(value)

################################################################################

def getProfitLists(trade):
    days = []
    profit = []
    for dayInfo in trade["History"]:
        days.append(dayInfo["Date"])
        profit.append(dayInfo["Profit"])
    return [days, profit]

################################################################################

def getAllTradeProfits(trades):
    allDict = {}
    for trade in trades:
        days, profit = getProfitLists(trade)
        for i in range(len(days)):
            try:
                allDict[days[i]] += profit[i]
            except:
                allDict[days[i]] = profit[i]
    allDict = dict(sorted(allDict.items()))
    return [list(allDict.keys()), list(allDict.values())]

################################################################################

def plotProfit(name: str, days, profit):
    plt.figure(figsize=(12, 6))
    plt.plot(days, profit, label=name, color='blue')
    
    plt.title(f"Profit")
    plt.xlabel("Date")
    plt.ylabel("Price (USD)")
    plt.grid(True, linestyle='--', alpha=0.5)
    plt.legend()
    
    plt.tight_layout()
    plt.show()

################################################################################

def getValueLists(trade):
    days = []
    value = []
    investment = []

    for dayInfo in trade["History"]:
        days.append(dayInfo["Date"])
        value.append(dayInfo["Value"])
        investment.append(trade["Total"])
    return [days, value, investment]

################################################################################

def getAllTradeValues(trades):
    allValuesDict = {}
    allInvestmentsDict = {}
    for trade in trades:
        days, value, investment = getValueLists(trade)
        for i in range(len(days)):
            try:
                allValuesDict[days[i]] += value[i]
                allInvestmentsDict[days[i]] += investment[i]
            except:
                allValuesDict[days[i]] = value[i]
                allInvestmentsDict[days[i]] = investment[i]
    allValuesDict = dict(sorted(allValuesDict.items()))
    allInvestmentsDict = dict(sorted(allInvestmentsDict.items()))
    return [list(allValuesDict.keys()), list(allValuesDict.values()), list(allInvestmentsDict.values())]

################################################################################

def plotValues(name: str, days, value, investment):
    plt.figure(figsize=(12, 6))
    plt.plot(days, value, label="Value", color='blue')
    plt.plot(days, investment, label="Principal", color='black')
    
    plt.title(f"Profit: {name}")
    plt.xlabel("Date")
    plt.ylabel("Price (USD)")
    plt.grid(True, linestyle='--', alpha=0.5)
    plt.legend()
    
    plt.tight_layout()
    plt.ylim(ymin=0)  # All the values should be positive, make the scaling better.
    plt.show()




################################################################################

# Main start
if __name__== "__main__":
    def list_of_strings(arg):
        return arg.split(',')
   
    parser = argparse.ArgumentParser()
    parser.add_argument("-t", "--trades", required=True, help="Json that defines the trades that were made.")
    parser.add_argument('--include', default=[], type=list_of_strings, help="Symbols to include (separated by commas, without spaces)")
    parser.add_argument('--exclude', default=[], type=list_of_strings, help="Symbols to exclude (separated by commas, without spaces)")
    parser.add_argument("-p", '--profit', action='store_true', help='Profit Only Plot')
    args = parser.parse_args()

    # Parse the documents that contain transactions.
    with open(args.trades, 'r') as f:
        # Get trade history from JSON file
        trades = json.load(f)

        # Filter by symbols
        if args.include != []:
            trades = includeSymbols(trades, args.include)
        if args.exclude != []:
            trades = excludeSymbols(trades, args.exclude)

        # Determine Stock Market symbols and the times to look up.
        startTime = determineOldestTradeTime(trades)
        startTimeStr = startTime.strftime("%Y-%m-%d")
        nowTimeStr = datetime.now().strftime("%Y-%m-%d")
        symbols = getSymbols(trades)

        # Get the stock market history information.
        history = {}
        for symbol in symbols:
            getStockHistory(symbol, startTimeStr, nowTimeStr, history)

        getProfitOverTime(trades, history)
        if args.profit:
            days, profit = getAllTradeProfits(trades)
            plotProfit("All", days, profit)
        else:
            days, value, investment = getAllTradeValues(trades)
            plotValues("All", days, value, investment)

        # print(trades[-1])

