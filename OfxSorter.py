import os
from datetime import datetime
from ofxparse import OfxParser
from ofxparse import Transaction
import codecs
import pandas as pd
import argparse
import json
import re

################################################################################

def getUniqueFileNameTimeStr():
   return datetime.now().strftime("%y%m%d%H%M%S")

TRANSACTION_KEYS = ["payee", "type", "date", "user_date", "amount", "id", "memo", "sic", "mcc", "checknum"]

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
      self.metaDataKeys = ["action", "type", "type", "name"]
      self.validActions = ['income', 'expense', 'move']

   def isInList(self, transToCheck):
      alreadyInList = False
      for trans in self.transList:
         if trans["raw"] == transToCheck:
            alreadyInList = True
            break
      return alreadyInList

   def addTransaction(self, transToAdd, docEntry, action: str):
      if not self.isInList(transToAdd):
         toAdd = {}
         toAdd["action"] = action
         toAdd["type"] = docEntry["type"]
         toAdd["name"] = docEntry["name"]
         toAdd["raw"] = transToAdd
         self.transList.append(toAdd)
         self.transactionsAdded += 1

   def modTransaction(self, transToMod, docEntry, action: str):
      for trans in self.transList:
         if trans["raw"] == transToMod:
            trans["action"] = action
            trans["type"] = docEntry["type"]
            trans["name"] = docEntry["name"]
            self.transactionsModified += 1

   def isMetaDataDifferent(self, transToCheck, docEntry, action: str):
      for trans in self.transList:
         if trans["raw"] == transToCheck:
            if trans["action"] != action or trans["type"] != docEntry["type"] or trans["name"] != docEntry["name"]:
               return True
      return False
            
   def isMetaDataActionValid(self, transToCheck):
      for trans in self.transList:
         if trans["raw"] == transToCheck:
            if trans["action"] not in self.validActions:
               return False
      return True
   
   def saveTransactions(self):
      print(f"Saving Transactions: {self.transactionsAdded} Transaction(s) added, {self.transactionsModified} Transaction(s) modified")
      if self.transactionsAdded > 0 or self.transactionsModified > 0:
         with open(self.pathToTransJson, 'w') as f:
            json.dump(self.transList, f)

   def makeTransactionSpreadsheet(self):
      # Function for adding to the dictionary.
      def transToPandaDict(theDict, dictKey: str, num: int, val: str):
         if dictKey not in theDict.keys():
            theDict[dictKey] = {}

         try:
            if dictKey == "amount":
               theDict[dictKey][num] = float(val)
            else:
               theDict[dictKey][num] = val
         except:
            pass
      
      # Fill in the dictionary
      transDicts = {}
      transNum = 0
      for trans in self.transList:
         for key in self.metaDataKeys:
            transToPandaDict(transDicts, 'meta.'+key, transNum, trans[key])
         for key in TRANSACTION_KEYS:
            transToPandaDict(transDicts, key, transNum, trans["raw"][key])
         transNum += 1

      # Save as Excel Spreadsheet via Pandas
      transData = pd.DataFrame(transDicts)
      transExcelPath = getUniqueFileNameTimeStr() + ".xlsx"
      transData.to_excel(transExcelPath)


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
               print(f"Meta Data Doesn't match {self.docsEntry["name"]} - type: {transaction.type} | payee: {transaction.payee} | date: {transaction.date} | amount: {transaction.amount}")
               # self.storedTrans.modTransaction(transactionDict, self.docsEntry, action)
            
            if not self.storedTrans.isMetaDataActionValid(transactionDict):
               print(f"Bad Action {self.docsEntry["name"]} - type: {transaction.type} | payee: {transaction.payee} | date: {transaction.date} | amount: {transaction.amount}")
               # if (ruleMatch and action == 'ask') or not ruleMatch:
               #    action = self.getAction(transaction, self.docsEntry["name"])
               # self.storedTrans.modTransaction(transactionDict, self.docsEntry, action)
            pass

   #############################################################################

   def getAction(self, transaction: Transaction, name: str):
      action = None
      while action == None:
         print(f"Need to label transaction {name} - type: {transaction.type} | payee: {transaction.payee} | date: {transaction.date} | amount: {transaction.amount}.")
         val = input("Select 'm' for moving money, 'i' for income, 'e' for expense > ")
         if val == 'm': action = 'move'
         elif val == 'i': action = 'income'
         elif val == 'e': action = 'expense'
         else: print("Invalid selection. Try again.")
      return action


################################################################################

# Main start
if __name__== "__main__":
   parser = argparse.ArgumentParser()
   parser.add_argument("-d", "--docs", help="Json that describes the documents to read.")
   parser.add_argument("-t", "--trans", help="Json contains all the previous parsed transactions.")
   args = parser.parse_args()

   allTrans = AllTransactions(args.trans)

   with open(args.docs, 'r') as f:
      docsEntries = json.load(f)
      for docsEntry in docsEntries:
         fullDir = os.path.join(os.path.dirname(args.docs), docsEntry["dir"])
         for fileName in os.listdir(fullDir):
            fileName = os.path.join(fullDir, fileName)
            if os.path.isfile(fileName):
               ext = os.path.splitext(fileName)[1].lower()
               if ext == '.ofx' or ext == '.qfx' or ext == '.qbo':
                  ofx = OfxSorter(fileName, allTrans, docsEntry)
                  ofx.importOfx()
                  ofx.applyRulesToTransactions()
   
   allTrans.saveTransactions()
   # allTrans.makeTransactionSpreadsheet()

