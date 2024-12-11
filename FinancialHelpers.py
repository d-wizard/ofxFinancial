from datetime import datetime

################################################################################

TRANSACTION_KEYS = ["payee", "type", "date", "user_date", "amount", "id", "memo", "sic", "mcc", "checknum"]

################################################################################

def getUniqueFileNameTimeStr():
   return datetime.now().strftime("%y%m%d%H%M%S")

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
