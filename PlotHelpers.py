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
