import os
import json
import argparse
from AllTransactions import AllTransactions
from OfxSorter import OfxSorter

################################################################################

# Main start
if __name__== "__main__":
   parser = argparse.ArgumentParser()
   parser.add_argument("-d", "--docs", required=True, help="Json that describes the documents to read.")
   parser.add_argument("-t", "--trans", required=True, help="Json contains all the previous parsed transactions.")
   parser.add_argument("-e", "--expenses", required=True, help="Json that defines how to categorize expenses.")
   args = parser.parse_args()

   # Import transactions from the json file.
   allTrans = AllTransactions(args.trans)

   # Parse the documents that contain transactions.
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
   
   # Categorize expenses based on the expenses json file.
   allTrans.categorizeExpenses(args.expenses)

   # Save transactions before exiting.
   allTrans.saveTransactions()