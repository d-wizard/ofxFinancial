import os
from datetime import datetime
from ofxparse import OfxParser
from ofxparse import Transaction
import codecs
import pandas as pd
import argparse
import json
import re
import matplotlib.pyplot as plt
import numpy as np

################################################################################

def getUniqueFileNameTimeStr():
   return datetime.now().strftime("%y%m%d%H%M%S")

TRANSACTION_KEYS = ["payee", "type", "date", "user_date", "amount", "id", "memo", "sic", "mcc", "checknum"]

################################################################################

def getMonthsInRange(start_inclusive: datetime, end_inclusive: datetime):
   def incrMonth(inVal: datetime):
      month = inVal.month
      year = inVal.year
      month += 1
      if month > 12:
         month = 1
         year += 1
      return datetime(year, month, 1)

   retVal = {}
   cur = datetime(start_inclusive.year, start_inclusive.month, 1)
   while cur <= end_inclusive:
      # Key is a specific month in a specific year
      key = cur.strftime("%y-%m")
      
      next = incrMonth(cur)
      retVal[key] = [cur,next]
      cur = next
   return retVal

################################################################################

def showBarPlot(dataDict: dict, barGroupLabels):
   
   numBarGroups = len(barGroupLabels)   
   numCategories = len(dataDict.items())
   barWidth = 1.0 / float(numCategories + 1)

   fig = plt.subplots()
   i = 0
   for key, val in dataDict.items():
      barPositions = [x + barWidth*float(i) for x in np.arange(numBarGroups) ]
      plt.bar(barPositions, val, width = barWidth, label = key) 
      i += 1

   labelOffset = -barWidth/2 #barWidth * float((numCategories - 1)/2)
   plt.xticks([r + labelOffset for r in range(numBarGroups)], barGroupLabels)

   plt.legend()
   plt.grid(True)
   plt.show()

################################################################################
################################################################################
################################################################################

class AllTransactions(object):
   def __init__(self, pathToTransJson: str):
      self.pathToTransJson = pathToTransJson
      try:
         with open(pathToTransJson, 'r') as f:
            self.transList = json.load(f)
      except:
         self.transList = []
      self.transactionsAdded = 0
      self.transactionsModified = 0
      self.metaDataKeys = ["action", "type", "type", "name", "category"]
      self.validActions = ['income', 'expense', 'move']

   #############################################################################

   def isInList(self, transToCheck):
      alreadyInList = False
      for trans in self.transList:
         if trans["raw"] == transToCheck:
            alreadyInList = True
            break
      return alreadyInList

   #############################################################################

   def addTransaction(self, transToAdd, docEntry, action: str):
      if not self.isInList(transToAdd):
         toAdd = {}
         toAdd["action"] = action
         toAdd["type"] = docEntry["type"]
         toAdd["name"] = docEntry["name"]
         toAdd["raw"] = transToAdd
         self.transList.append(toAdd)
         self.transactionsAdded += 1

   #############################################################################

   def modTransaction(self, transToMod, docEntry, action: str):
      for trans in self.transList:
         if trans["raw"] == transToMod:
            trans["action"] = action
            trans["type"] = docEntry["type"]
            trans["name"] = docEntry["name"]
            self.transactionsModified += 1

   #############################################################################

   def modCategory(self, transToMod, category: str):
      for trans in self.transList:
         if trans["raw"] == transToMod:
            trans["category"] = category
            self.transactionsModified += 1

   #############################################################################

   def isMetaDataDifferent(self, transToCheck, docEntry, action: str):
      for trans in self.transList:
         if trans["raw"] == transToCheck:
            if trans["action"] != action or trans["type"] != docEntry["type"] or trans["name"] != docEntry["name"]:
               return True
      return False
            
   #############################################################################

   def isMetaDataActionValid(self, transToCheck):
      for trans in self.transList:
         if trans["raw"] == transToCheck:
            if trans["action"] not in self.validActions:
               return False
      return True
   
   #############################################################################

   def getTransActionDateTime(self, trans) -> datetime:
      return datetime.strptime(trans['raw']['date'], '%Y-%m-%d %H:%M:%S')

   #############################################################################

   def saveTransactions(self):
      print(f"Saving Transactions: {self.transactionsAdded} Transaction(s) added, {self.transactionsModified} Transaction(s) modified")
      if self.transactionsAdded > 0 or self.transactionsModified > 0:
         with open(self.pathToTransJson, 'w') as f:
            json.dump(self.transList, f)
         
         altPath = os.path.splitext(self.pathToTransJson)[0] + "_" + getUniqueFileNameTimeStr() + ".json"
         with open(altPath, 'w') as f:
            json.dump(self.transList, f)

   #############################################################################

   def makeTransactionSpreadsheet(self, savePath: str):
      # Function for adding to the dictionary.
      def transToPandaDict(theDict, dictKey: str, num: int, valDict, valKey: str):
         if dictKey not in theDict.keys():
            theDict[dictKey] = {}

         try:
            if dictKey == "amount":
               theDict[dictKey][num] = float(valDict[valKey])
            else:
               theDict[dictKey][num] = valDict[valKey]
         except:
            pass
      
      # Fill in the dictionary
      transDicts = {}
      transNum = 0
      for trans in self.transList:
         for key in self.metaDataKeys:
            transToPandaDict(transDicts, 'meta.'+key, transNum, trans, key)
         for key in TRANSACTION_KEYS:
            transToPandaDict(transDicts, key, transNum, trans["raw"], key)
         transNum += 1

      # Save as Excel Spreadsheet via Pandas
      transData = pd.DataFrame(transDicts)
      transData.to_excel(savePath)

   #############################################################################

   def getActionStats(self, action: str):
      stats = {'oldest': None, 'newest': None, 'count': 0}
      for trans in self.transList:
         if trans['action'] == action:
            date = self.getTransActionDateTime(trans)
            if stats['oldest'] == None: stats['oldest'] = date
            elif date < stats['oldest']: stats['oldest'] = date
            if stats['newest'] == None: stats['newest'] = date
            elif date > stats['newest']: stats['newest'] = date
            stats['count'] += 1
      return stats

   #############################################################################

   def getActionMonthlyBreakdown(self, action: str, categories = []):
      stats = self.getActionStats(action)
      months = getMonthsInRange(stats['oldest'], stats['newest'])

      return self.getActionBreakdown(months, action, categories)

   #############################################################################

   def getActionBreakdown(self, timeRanges, action: str, categories = []):
      retVal = {}
      parseCount = 0
      for key, thisTimeRange in timeRanges.items():
         retVal[key] = 0 # Start at 0 dollars than add each matching transaction amount.

         # Filter out non-matching transactions
         transList = self.transList
         transList = self.filterByDateRange(transList, thisTimeRange[0], thisTimeRange[1])
         transList = self.filterByAction(transList, action)
         if len(categories) > 0:
            transList = self.filterByCategories(transList, categories)

         # Sum up matching transactions
         for trans in transList:
            retVal[key] += float(trans['raw']['amount'])
            parseCount += 1

      return retVal
   
   #############################################################################

   def plotActionBreakdown(self, timeRanges, action: str, categories = []):

      categorySumsByTimeRange = {} # Dict of lists. Each dict key is a category. Each items is a list of monthly sums.
      if len(categories) > 0:
         for catName in categories:
            categorySumsByTimeRange[catName] = [] # Initialize to an empty list
            for i in range(len(timeRanges.items())):
               categorySumsByTimeRange[catName].append(0)
      else:
         categorySumsByTimeRange['all'] = [] # Initialize to an empty list
         for i in range(len(timeRanges.items())):
            categorySumsByTimeRange['all'].append(0)

      timeIndex = 0
      labels = []
      for key, thisTimeRange in timeRanges.items():
         # Filter out non-matching transactions
         transList = self.transList
         transList = self.filterByDateRange(transList, thisTimeRange[0], thisTimeRange[1])
         transList = self.filterByAction(transList, action)
         if len(categories) > 0:
            for trans in transList:
               if trans['category'] in categories:
                  categorySumsByTimeRange[trans['category']][timeIndex] += float(trans['raw']['amount'])
         else:
            # Take all 
            for trans in transList:
               categorySumsByTimeRange['all'][timeIndex] += float(trans['raw']['amount'])

         timeIndex += 1
         labels.append(key)

      if action == "expense":
         # expenses are negative. Negate them to be positive.
         for key, val in categorySumsByTimeRange.items():
            for i in range(len(categorySumsByTimeRange[key])):
               categorySumsByTimeRange[key][i] = -categorySumsByTimeRange[key][i]

      showBarPlot(categorySumsByTimeRange, labels)


   #############################################################################

   def filterByDateRange(self, transList, startInclusive: datetime = None, stopExclusive: datetime = None):
      retVal = []
      for trans in transList:
         date = self.getTransActionDateTime(trans)
         if (startInclusive == None or date >= startInclusive) and (stopExclusive == None or date < stopExclusive):
            retVal.append(trans)
      return retVal

   #############################################################################

   def filterByAction(self, transList, action: str):
      retVal = []
      for trans in transList:
         if trans['action'] == action:
            retVal.append(trans)
      return retVal

   #############################################################################

   def filterByCategories(self, transList, categories):
      retVal = []
      for trans in transList:
         if trans['category'] in categories:
            retVal.append(trans)
      return retVal
               
   #############################################################################

   def plotBreakdown(self, breakdown):
      x = []
      y = []
      labels = []
      count = 1
      for key, value in breakdown.items():
         labels.append(key)
         y.append(value)
         x.append(count)
         count += 1

      # Create the plot
      plt.plot(x, y)

      # Set the x-axis labels
      plt.xticks(x, labels)

      # Add title and axis labels
      # plt.title("Plot with Labeled X-Axis")
      # plt.xlabel("Categories")
      # plt.ylabel("Values")

      # Show the plot
      plt.show()

   #############################################################################

   def categorizeExpenses(self, expensesJsonPath, defaultCat = 'ask'):
      with open(expensesJsonPath, 'r') as f:
         expCatDict = json.load(f)
         transList = self.filterByAction(self.transList, "expense")
         categories = expCatDict["categories"]

         for trans in transList:
            ruleMatch = False
            expenseCat = defaultCat
            for rule in expCatDict['rules']:
               checks = rule[0]
               cat = rule[1]
               ruleMatch = True # start True, must pass each check
               for check in checks:
                  transKey, transMatchStr = list(check.items())[0]
                  transVal = trans['raw'][transKey]
                  if transKey == 'amount': # Amount is special, can do greater than, less than, equal, etc
                     cmd, val = transMatchStr.split(' ')
                     amount = -float(transVal) # expenses are negative values so negate
                     val = float(val)
                     if cmd == '>' and not (amount > val): ruleMatch = False
                     elif  cmd == '>=' and not (amount >= val): ruleMatch = False
                     elif  cmd == '==' and not (amount == val): ruleMatch = False
                     elif  cmd == '<=' and not (amount <= val): ruleMatch = False
                     elif  cmd == '<' and not (amount < val): ruleMatch = False
                  elif not re.match(transMatchStr, transVal):
                     ruleMatch = False
               if ruleMatch:
                  expenseCat = cat
                  break

            # Update the category associated with this expense.
            try:
               curCat = trans['category']
            except:
               curCat = None

            if expenseCat == 'ask' and curCat == None:
               expenseCat = self.getCategory(trans, categories)
               self.modCategory(trans['raw'], expenseCat)
            elif curCat == None:
               self.modCategory(trans['raw'], expenseCat) # No category yet, add it here.
            elif expenseCat != 'ask' and expenseCat != curCat:
               print(f'Current Expense Category: {curCat} | Rule says: {expenseCat}')

   #############################################################################

   def getCategory(self, trans, categories):
      retVal = None
      while retVal == None:
         print(f"Need to categorize: {trans['name']} - type: {trans['raw']['type']} | payee: {trans['raw']['payee']} | date: {trans['raw']['date']} | amount: {trans['raw']['amount']}.")
         selectStr = "Select the number that matches the category: "
         selectNum = 0
         selectDict = {}
         for cat in categories:
            selectStr += f"{cat}({selectNum})', "
            selectDict[selectNum] = cat
            selectNum += 1

         val = input(selectStr + " > ")
         try:
             if int(val) >= 0 and int(val) < selectNum:
                retVal = selectDict[int(val)]
         except:
            pass
         if (retVal == None): print("Invalid selection. Try again.")
      return retVal

   #############################################################################


################################################################################
################################################################################
################################################################################

class OfxSorter(object):
   def __init__(self, pathToOfxFile: str, storedTrans: AllTransactions, docsEntry):
      self.pathToOfxFile = pathToOfxFile
      self.storedTrans = storedTrans
      self.docsEntry = docsEntry

   #############################################################################

   def importOfx(self):
      self.fixOfxFile(self.pathToOfxFile)
      with codecs.open(self.pathToOfxFile) as fileobj:
         self.ofxObj = OfxParser.parse(fileobj)

   #############################################################################

   def fixOfxFile(self, path):
      # Define the function that will add a new line before the search str (in there isn't already a new line before it)
      def startFirstEntryOnNewLine(inStr: str, searchStr: str):
         try:
            newLine = "\r\n" if inStr.find("\r\n") >= 0 else "\n"
            pos = inStr.find(searchStr)
            if pos > 0:
               if inStr[pos-1] != "\n":
                  inStr = inStr[:pos] + newLine + inStr[pos:]
         except:
            pass
         return inStr

      # Read the file.
      fileId = open(path, 'r')
      ofx = fileId.read()
      fileId.close()

      # Certain strings in the header need to start on new lines to be parsed by OfxParser. These are the strings.
      needToStartOnNewLineStrs = ["DATA:", "VERSION:", "SECURITY:", "ENCODING:", "CHARSET:", "COMPRESSION:", "OLDFILEUID:", "NEWFILEUID:", "<OFX>"]
      fixed = ofx
      for searchStr in needToStartOnNewLineStrs:
         fixed = startFirstEntryOnNewLine(fixed, searchStr)

      # Save the file (only if it is changing).
      if fixed != ofx:
         fileId = open(path, 'w')
         fileId.write(fixed)
         fileId.close()

   #############################################################################

   def getTransactionVal(self, trans: Transaction, key: str):
      try:
         if key == "payee": return trans.payee
         if key == "type": return trans.type
         if key == "date": return trans.date
         if key == "user_date": return trans.user_date
         if key == "amount": return trans.amount
         if key == "id": return trans.id
         if key == "memo": return trans.memo
         if key == "sic": return trans.sic
         if key == "mcc": return trans.mcc
         if key == "checknum": return trans.checknum
      except:
         return None

   #############################################################################

   def getTransactionDict(self, trans: Transaction):
      retVal = {}
      for key in TRANSACTION_KEYS:
         retVal[key] = str(self.getTransactionVal(trans, key))
      return retVal
   
   #############################################################################

   def transactionsToExcel(self):
      # Function for adding to the dictionary.
      def transToPandaDict(theDict, dictKey: str, num: int, val: str):
         try:
            if dictKey == "amount":
               theDict[dictKey][num] = float(val)
            else:
               theDict[dictKey][num] = val
         except:
            pass
      
      # Initialize the dictionary
      transDicts = {}
      for key in TRANSACTION_KEYS:
         transDicts[key] = {}

      # Fill in the dictionary
      account = self.ofxObj.account
      statement = account.statement
      transNum = 0
      for transaction in statement.transactions:
         for key in TRANSACTION_KEYS:
            transToPandaDict(transDicts, key, transNum, self.getTransactionVal(transaction, key))
         transNum += 1

      # Save as Excel Spreadsheet via Pandas
      transData = pd.DataFrame(transDicts)
      transExcelPath = os.path.splitext(self.pathToOfxFile)[0] + "_" + getUniqueFileNameTimeStr() + ".xlsx"
      transData.to_excel(transExcelPath)

   #############################################################################

   def applyRulesToTransactions(self):
      account = self.ofxObj.account
      statement = account.statement
      rulesList = self.docsEntry["rules"]
      for transaction in statement.transactions:
         transactionDict = self.getTransactionDict(transaction)

         # Check transaction against all the rules for categorizing them.
         ruleMatch = False
         for rule in rulesList:
            checks = rule[0]
            action = rule[1]
            ruleMatch = True # start True, must pass each check
            for check in checks:
               transKey, transMatchStr = list(check.items())[0]
               transVal = transactionDict[transKey]
               if not re.match(transMatchStr, transVal):
                  ruleMatch = False
            if ruleMatch:
               break
         
         alreadyCategorized = self.storedTrans.isInList(transactionDict)
         if not alreadyCategorized:
            if (ruleMatch and action == 'ask') or not ruleMatch:
               action = self.getAction(transaction, self.docsEntry["name"])
            self.storedTrans.addTransaction(transactionDict, self.docsEntry, action)
         else:
            # Transaction has been categorized. Check for changes.
            if ruleMatch and action != 'ask' and self.storedTrans.isMetaDataDifferent(transactionDict, self.docsEntry, action):
               print(f"Meta Data Doesn't match: {self.docsEntry["name"]} - type: {transaction.type} | payee: {transaction.payee} | date: {transaction.date} | amount: {transaction.amount}")
               # self.storedTrans.modTransaction(transactionDict, self.docsEntry, action)
            
            if not self.storedTrans.isMetaDataActionValid(transactionDict):
               print(f"Bad Action: {self.docsEntry["name"]} - type: {transaction.type} | payee: {transaction.payee} | date: {transaction.date} | amount: {transaction.amount}")
               # if (ruleMatch and action == 'ask') or not ruleMatch:
               #    action = self.getAction(transaction, self.docsEntry["name"])
               # self.storedTrans.modTransaction(transactionDict, self.docsEntry, action)
            pass

   #############################################################################

   def getAction(self, transaction: Transaction, name: str):
      action = None
      while action == None:
         print(f"Need to label transaction: {name} - type: {transaction.type} | payee: {transaction.payee} | date: {transaction.date} | amount: {transaction.amount}.")
         val = input("Select 'm' for moving money, 'i' for income, 'e' for expense > ")
         if val == 'm': action = 'move'
         elif val == 'i': action = 'income'
         elif val == 'e': action = 'expense'
         else: print("Invalid selection. Try again.")
      return action


def showPlot():
   # set width of bar 
   barWidth = 0.25
   fig = plt.subplots()#figsize =(12, 8)) 

   # set height of bar 
   IT = [12.5, 30, 1, 8, 22] 
   ECE = [28, 6, 16, 5, 10] 
   CSE = [29, 3, 24, 25, 17] 

   # Set position of bar on X axis 
   br1 = np.arange(len(IT)) 
   br2 = [x + barWidth for x in br1] 
   br3 = [x + barWidth for x in br2] 

   # Make the plot

   print(br1)
   print(IT)
   plt.bar(br1, IT, #color ='r', 
           width = barWidth, 
         # edgecolor ='grey', 
         label ='IT') 
   print(br2)
   plt.bar(br2, ECE, #color ='g', 
           width = barWidth, 
         # edgecolor ='grey', 
         label ='ECE') 
   print(br3)
   plt.bar(br3, CSE, #color ='b', 
           width = barWidth, 
         # edgecolor ='grey', 
         label ='CSE') 

   # Adding Xticks 
   # plt.xlabel('Branch', fontweight ='bold', fontsize = 15) 
   # plt.ylabel('Students passed', fontweight ='bold', fontsize = 15) 
   # plt.xticks([r + barWidth for r in range(len(IT))], 
   #       ['2015', '2016', '2017', '2018', '2019'])

   plt.legend()
   plt.show()

################################################################################

# Main start
if __name__== "__main__":
   parser = argparse.ArgumentParser()
   parser.add_argument("-d", "--docs", help="Json that describes the documents to read.")
   parser.add_argument("-t", "--trans", help="Json contains all the previous parsed transactions.")
   parser.add_argument("-e", "--expenses", help="Json that defines how to categorize expenses.")
   parser.add_argument("-x", "--excel", help="Path to save spreadsheet to.")
   args = parser.parse_args()

   # showPlot()

   allTrans = AllTransactions(args.trans)
   stats = allTrans.getActionStats('expense')
   months = getMonthsInRange(stats['oldest'], stats['newest'])
   allTrans.plotActionBreakdown(months, 'expense')#, ["taxes", "insurance", "utilities", "medical", "home_auto", "entertainment", "misc"])

# allTrans = AllTransactions(args.trans)
# allTrans.plotBreakdown(allTrans.getActionMonthlyBreakdown('expense', ["home_auto", "entertainment", "misc"]))

   # if args.docs != None:
   #    with open(args.docs, 'r') as f:
   #       docsEntries = json.load(f)
   #       for docsEntry in docsEntries:
   #          fullDir = os.path.join(os.path.dirname(args.docs), docsEntry["dir"])
   #          for fileName in os.listdir(fullDir):
   #             fileName = os.path.join(fullDir, fileName)
   #             if os.path.isfile(fileName):
   #                ext = os.path.splitext(fileName)[1].lower()
   #                if ext == '.ofx' or ext == '.qfx' or ext == '.qbo':
   #                   ofx = OfxSorter(fileName, allTrans, docsEntry)
   #                   ofx.importOfx()
   #                   ofx.applyRulesToTransactions()
   

   # if args.expenses != None:
   #    allTrans.categorizeExpenses(args.expenses)

   # if args.excel != None:
   #    # If just a directory is specified generated the file name.
   #    path = args.excel if not os.path.isdir(args.excel) else os.path.join(args.excel, "transactions_" + getUniqueFileNameTimeStr() + ".xlsx")
   #    allTrans.makeTransactionSpreadsheet(path)

   # # Save transactions before exiting.
   # allTrans.saveTransactions()