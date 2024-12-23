import os
import argparse
from datetime import datetime, timedelta
from AllTransactions import AllTransactions
from FinancialHelpers import *

################################################################################

def getDateTimeFromCmdLineArg(arg: str):
   delimCount = arg.count(":")
   if delimCount == 0:
      return datetime.strptime(arg, '%y')
   elif delimCount == 1:
      return datetime.strptime(arg, '%y:%m')
   elif delimCount == 2:
      return datetime.strptime(arg, '%y:%m:%d')
   return None

################################################################################

# Main start
if __name__== "__main__":
   def list_of_strings(arg):
      return arg.split(',')

   parser = argparse.ArgumentParser()
   parser.add_argument("-t", "--trans", required=True, help="Json contains all the previous parsed transactions.")
   parser.add_argument("-S", "--start", help="Time Range Start (inclusive). Format is YY (for year only), YY:MM (year and month), YY:MM:DD (down to the day).")
   parser.add_argument("-E", "--end", help="Time Range End (inclusive). Format is YY (for year only), YY:MM (year and month), YY:MM:DD (down to the day).")
   parser.add_argument("-Y", "--years", type=float, help="How many years in the range.")
   parser.add_argument("-M", "--months", type=float, help="How many month in the range.")
   parser.add_argument("-x", "--excel", help="Path to save spreadsheet to.")
   parser.add_argument("-e", "--expenses_plot", action='store_true', help="Plot expenses.")
   parser.add_argument('--categories', default=[], type=list_of_strings, help="Categories to plot (separated by commas, without spaces)")

   args = parser.parse_args()

   # Convert absolute time args to datetime.
   if args.end != None:
      args.end = getDateTimeFromCmdLineArg(args.end) # Convert to datetime
   if args.start != None:
      args.start = getDateTimeFromCmdLineArg(args.start) # Convert to datetime

   # If neither start nor end is specified, assume end is right now.
   if args.end == None and args.start == None:
      args.end = datetime.now()

   # If only start or end is specified and years/months is specified, compute the missing param (among start/end)
   if args.start != None and args.end == None:
      # Start is specified, but end isn't. Try to use years / months args to compute end.
      if args.years != None:
         args.end = args.start + timedelta(days=(args.years*365.24))
      elif args.months != None:
         args.end = args.start + timedelta(days=(args.months*365.24/12.0))
   elif args.start == None and args.end != None:
      # End is specified, but start isn't. Try to use years / months args to compute start.
      if args.years != None:
         args.start = args.end - timedelta(days=(args.years*365.24))
      elif args.months != None:
         args.start = args.end - timedelta(days=(args.months*365.24/12.0))

   # Import transactions from the json file.
   allTrans = AllTransactions(args.trans)
   allTrans.pruneByDateRange(args.start, args.end)

   if args.excel != None:
      # If just a directory is specified generated the file name.
      path = args.excel if not os.path.isdir(args.excel) else os.path.join(args.excel, "transactions_" + getUniqueFileNameTimeStr() + ".xlsx")
      allTrans.makeTransactionSpreadsheet(path)

   if args.expenses_plot:
      stats = allTrans.getActionStats('expense')
      months = getMonthsInRange(stats['oldest'], stats['newest'])
      allTrans.plotActionBreakdown(months, 'expense', args.categories)