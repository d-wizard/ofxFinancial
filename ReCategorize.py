import os
import json
import argparse
from AllTransactions import AllTransactions
from OfxSorter import OfxSorter

################################################################################

# Main start
if __name__== "__main__":
   parser = argparse.ArgumentParser()
   parser.add_argument("-c", "--category", default=None, help="The name of the category to move transactions from.")
   parser.add_argument("-t", "--trans", required=True, help="Json contains all the previous parsed transactions.")
   parser.add_argument("-e", "--expenses", required=True, help="Json that defines how to categorize expenses.")
   args = parser.parse_args()

   # Import transactions from the json file.
   allTrans = AllTransactions(args.trans)

   # Categorize expenses based on the expenses json file.
   if args.category != None:
      allTrans.removeCategory(args.category)
   allTrans.categorizeExpenses(args.expenses, reCategorize=True)

   # Save transactions before exiting.
   allTrans.saveTransactions()
