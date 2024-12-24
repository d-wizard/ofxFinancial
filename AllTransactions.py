import os
import json
import pandas as pd
import re
from datetime import datetime
from FinancialHelpers import *
import PlotHelpers

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
         transList = self.__filterByDateRange(transList, thisTimeRange[0], thisTimeRange[1])
         transList = self.__filterByAction(transList, action)
         if len(categories) > 0:
            transList = self.__filterByCategories(transList, categories)

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
         transList = self.__filterByDateRange(transList, thisTimeRange[0], thisTimeRange[1])
         transList = self.__filterByAction(transList, action)
         if len(categories) > 0:
            for trans in transList:
               if trans['category'] in categories:
                  categorySumsByTimeRange[trans['category']][timeIndex] += float(trans['raw']['amount'])
               elif 'else' in categories: # group all other categories together
                  categorySumsByTimeRange['else'][timeIndex] += float(trans['raw']['amount'])
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

      PlotHelpers.showBarPlot(categorySumsByTimeRange, labels)

   #############################################################################

   def __filterByDateRange(self, transList, startInclusive: datetime = None, stopExclusive: datetime = None):
      retVal = []
      for trans in transList:
         date = self.getTransActionDateTime(trans)
         if (startInclusive == None or date >= startInclusive) and (stopExclusive == None or date < stopExclusive):
            retVal.append(trans)
      return retVal

   #############################################################################

   def pruneByDateRange(self, startInclusive: datetime = None, stopExclusive: datetime = None): # Permanent version of __filterByDateRange
      self.transList = self.__filterByDateRange(self.transList, startInclusive, stopExclusive)

   #############################################################################

   def __filterByAction(self, transList, action: str):
      retVal = []
      for trans in transList:
         if trans['action'] == action:
            retVal.append(trans)
      return retVal

   #############################################################################

   def pruneByDateAction(self, action: str): # Permanent version of __filterByAction
      self.transList = self.__filterByAction(self.transList, action)

   #############################################################################

   def __filterByCategories(self, transList, categories):
      retVal = []
      for trans in transList:
         if trans['category'] in categories:
            retVal.append(trans)
      return retVal

   #############################################################################

   def pruneByCategories(self, categories): # Permanent version of __filterByCategories
      self.transList = self.__filterByCategories(self.transList, categories)
               
   #############################################################################

   def categorizeExpenses(self, expensesJsonPath, defaultCat = 'ask'):
      with open(expensesJsonPath, 'r') as f:
         expCatDict = json.load(f)
         transList = self.__filterByAction(self.transList, "expense")
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
               expenseCat = self.__askUserForCategory(trans, categories)
               self.modCategory(trans['raw'], expenseCat)
            elif curCat == None:
               self.modCategory(trans['raw'], expenseCat) # No category yet, add it here.
            elif expenseCat != 'ask' and expenseCat != curCat:
               print(f'Current Expense Category: {curCat} | Rule says: {expenseCat}')

   #############################################################################

   def __askUserForCategory(self, trans, categories):
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
