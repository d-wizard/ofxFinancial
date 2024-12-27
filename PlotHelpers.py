import matplotlib.pyplot as plt
import numpy as np

################################################################################
################################################################################
################################################################################

def showBarPlot(dataDict: dict, barGroupLabels):
   
   numBarGroups = len(barGroupLabels)   
   numCategories = len(dataDict.items())
   barWidth = 1.0 / float(numCategories)

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

def showBarPlotAlt(dataDict: dict, barGroupLabels):
   
   numBarGroups = len(barGroupLabels)   
   numCategories = len(dataDict.items())
   totalBarWidth = 0.8
   barOffset = 0
   barWidth = totalBarWidth / float(numCategories)

   fig = plt.subplots()
   i = 0
   for key, val in dataDict.items():
      barPositions = [barOffset + x + barWidth*float(i) for x in np.arange(numBarGroups) ]
      plt.bar(barPositions, val, width = barWidth, label = key) 
      i += 1

   labelOffset = (numCategories-1.0)*barWidth/2
   plt.xticks([r + labelOffset for r in range(numBarGroups)], barGroupLabels)

   plt.legend()
   plt.grid(axis='y')
   plt.show()

################################################################################

def showStackedBarPlot(dataDict: dict, barGroupLabels):
   
   numBarGroups = len(barGroupLabels)   
   barPositions = np.arange(numBarGroups)
   barWidth = 0.60

   fig = plt.subplots()
   bottom = [0] * numBarGroups
   for key, val in dataDict.items():
      plt.bar(barPositions, val, bottom = bottom, width = barWidth, label = key)
      for i in range(len(val)):
         bottom[i] += val[i]

   plt.xticks(barPositions, barGroupLabels)

   plt.legend()
   plt.grid(axis='y')
   plt.show()