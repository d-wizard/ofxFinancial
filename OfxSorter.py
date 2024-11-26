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

################################################################################

class OfxSorter(object):
   def __init__(self, pathToOfxFile: str):
      self.pathToOfxFile = pathToOfxFile

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

   def printTransactions(self):
      payees = {}
      types = {}
            
      account = self.ofxObj.account
      statement = account.statement
      for transaction in statement.transactions:
         try:
            payees[transaction.payee] += 1
         except:
            payees[transaction.payee] = 1
         try:
            types[transaction.type] += 1
         except:
            types[transaction.type] = 1

      print(types)
      print(payees)

   #############################################################################

   def transactionsToExcel(self):
      # Function for adding to the dictionary.
      def transToDict(theDict, dictKey: str, num: int, val: str):
         try:
            if dictKey == "amount":
               theDict[dictKey][num] = float(val)
            else:
               theDict[dictKey][num] = val
         except:
            pass
      
      # Initialize the dictionary
      keys = ["payee", "type", "date", "user_date", "amount", "id", "memo", "sic", "mcc", "checknum"]
      transDicts = {}
      for key in keys:
         transDicts[key] = {}

      # Fill in the dictionary
      account = self.ofxObj.account
      statement = account.statement
      transNum = 0
      for transaction in statement.transactions:
         for key in keys:
            transToDict(transDicts, key, transNum, self.getTransactionVal(transaction, key))
         transNum += 1

      # Save as Excel Spreadsheet via Pandas
      transData = pd.DataFrame(transDicts)
      transExcelPath = os.path.splitext(self.pathToOfxFile)[0] + "_" + getUniqueFileNameTimeStr() + ".xlsx"
      transData.to_excel(transExcelPath)

   #############################################################################

   def applyRulesToTransactions(self, rulesList):
      account = self.ofxObj.account
      statement = account.statement
      for transaction in statement.transactions:
         match = False
         for rule in rulesList:
            checks = rule[0]
            action = rule[1]
            match = True # start True, must pass each check
            for check in checks:
               transKey, transMatchStr = list(check.items())[0]
               transVal = self.getTransactionVal(transaction, transKey)
               if not re.match(transMatchStr, transVal):
                  match = False
            if match:
               break
         if (match and action == 'ask') or not match:
            print(f"Trans - type: {transaction.type} | payee: {transaction.payee} | date: {transaction.date} | amount: {transaction.amount}")



################################################################################

# Main start
if __name__== "__main__":
   parser = argparse.ArgumentParser()
   parser.add_argument("-p", "--path", help="File / Folder to process")
   args = parser.parse_args()

   try:
      if os.path.isfile(args.path):
         ofx = OfxSorter(args.path)
         ofx.importOfx()
         ofx.transactionsToExcel()
   except:
      print("Need to specify input file/folder")
   