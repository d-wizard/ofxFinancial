import matplotlib.pyplot as plt
import numpy as np
import math
import colorsys

class betterColors:
   goldenAngle = 137.5 / 360 # normalize

   def __init__(self, h=0.1, s=1, v=0.98):
      self._h = h
      self._s = s
      self._v = v

   def get_next_color(self, ):
      retVal = self.hsv_to_hex_rgb(self._h, self._s, self._v)
      self._h += self.goldenAngle
      self._s += (math.pi/6.0)
      self._v += (math.pi/15.0)
      if self._s > 1:
         self._s -= (math.e / 4.5)
      if self._v > 1:
         self._v -= (math.e / 11)
      print(retVal)
      return retVal

   def hsv_to_hex_rgb(self, h, s, v):
      """
      Converts HSV values (0-1 range) to a hexadecimal RGB string (#RRGGBB).

      Args:
         h (float): Hue, in the range [0, 1].
         s (float): Saturation, in the range [0, 1].
         v (float): Value, in the range [0, 1].

      Returns:
         str: A string representing the color in hexadecimal RGB format (e.g., "#FF0000").
      """
      # Modify hue to give better color separation.
      cosScalar = 0.025
      h2pi = h * math.pi * 2.0
      h += ((math.cos(h2pi * 6) - 1.0) * cosScalar)
      while(h < 0):
         h += 1.0

      # Convert HSV (0-1) to RGB (0-1)
      r, g, b = colorsys.hsv_to_rgb(h, s, v)

      # Scale RGB values to 0-255 and convert to integers
      r_int = int(r * 255)
      g_int = int(g * 255)
      b_int = int(b * 255)

      # Format as a hexadecimal string
      hex_rgb = f"#{r_int:02X}{g_int:02X}{b_int:02X}"
      return hex_rgb

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

   fig, ax = plt.subplots()
   i = 0
   for key, val in dataDict.items():
      barPositions = [barOffset + x + barWidth*float(i) for x in np.arange(numBarGroups) ]
      plt.bar(barPositions, val, width = barWidth, label = key) 
      i += 1

   labelOffset = (numCategories-1.0)*barWidth/2
   plt.xticks([r + labelOffset for r in range(numBarGroups)], barGroupLabels)

   plt.legend()
   plt.grid(axis='y')
   ax.format_coord = lambda x, y: '{:0.2f}'.format(y)
   plt.show()

################################################################################

def showStackedBarPlot(dataDict: dict, barGroupLabels):
   
   numBarGroups = len(barGroupLabels)   
   barPositions = np.arange(numBarGroups)
   barWidth = 0.60

   fig, ax = plt.subplots()
   bottom = [0] * numBarGroups
   colors = betterColors()
   for key, val in dataDict.items():
      plt.bar(barPositions, val, bottom = bottom, width = barWidth, label = key, color=colors.get_next_color())
      for i in range(len(val)):
         bottom[i] += val[i]

   plt.xticks(barPositions, barGroupLabels)

   plt.legend()
   plt.grid(axis='y')
   ax.format_coord = lambda x, y: '{:0.2f}'.format(y)
   plt.show()