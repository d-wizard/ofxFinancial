import os
from ofxparse import OfxParser
import codecs

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

################################################################################

# Main start
if __name__== "__main__":
   ofx = OfxSorter("F:\Financial\docs\WF_Checking\Checking1_241125.qfx")
   ofx.importOfx()
   ofx.printTransactions()