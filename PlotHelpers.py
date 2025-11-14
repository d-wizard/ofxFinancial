import matplotlib.pyplot as plt
import numpy as np
import math
import colorsys

# Hue BMP Gen code
try:
   from PIL import Image
except:
   pass


class betterColors:
   goldenAngle = 137.5 / 360 # normalize

   def __init__(self, h=0.1, s=1, v=0.98):
      self._h = h
      self._s = s
      self._v = v

   def get_next_color(self, ):
      retVal = self.hsv_to_rgb_hex(self._h, self._s, self._v, True)
      self._h += self.goldenAngle
      self._s += (math.pi/6.0)
      self._v += (math.pi/15.0)
      if self._s > 1:
         self._s -= (math.e / 4.5)
      if self._v > 1:
         self._v -= (math.e / 11)
      print(retVal)
      return retVal

   def quarterCircle(self, val: float):
      # Bound
      val = 1.0 if val > 1.0 else val
      val = 0.0 if val < 0.0 else val
      
      # The equation for a quarter circle: y=(1 - (1-x)^2)^0.5
      # http://www.wolframalpha.com/input/?i=y%3D%281+-+%281-x%29%5E2%29%5E0.5+from+x%3D0+to+1
      return math.sqrt(1.0 - math.pow(1.0 - val, 2))

   def betterHue(self, hue: float):
      oneSixth = 1.0 / 6.0

      # Determine which sixth of the hue we are in.
      whichSixth = int(hue / oneSixth)
      remainderInSixth = hue - float(whichSixth) * oneSixth
      direction = whichSixth & 1

      # Setup for scaling
      scaledRemainder = remainderInSixth * 6.0 # Convert from 0 to 1/6th to 0 to 1
      scaledPower = 2.0 # 2 = square the value, 3 = cube the value, 0.5 = square root, etc

      # Do the math to determine the scaling.
      scaledRemainder = 1.0 - scaledRemainder if direction else scaledRemainder # Mirror on odd sixths
      scaledRemainder = self.quarterCircle(scaledRemainder)
      scaledRemainder = math.pow(scaledRemainder, scaledPower) # Use power to better scale
      scaledRemainder = 1.0 - scaledRemainder if direction else scaledRemainder # Mirror back on odd sixths

      scaledRemainder *= oneSixth # Scale back down to 1/6th
      
      return float(whichSixth)*oneSixth + scaledRemainder


   def hsv_to_rgb_bytes(self, h, s, v):

      # Convert HSV (0-1) to RGB (0-1)
      r, g, b = colorsys.hsv_to_rgb(h, s, v)

      # Scale RGB values to 0-255 and convert to integers
      r_int = int(r * 255)
      g_int = int(g * 255)
      b_int = int(b * 255)

      return (r_int, g_int, b_int)


   def hsv_to_rgb_hex(self, h, s, v, applyBetterHue = False):
      """
      Converts HSV values (0-1 range) to a hexadecimal RGB string (#RRGGBB).

      Args:
         h (float): Hue, in the range [0, 1].
         s (float): Saturation, in the range [0, 1].
         v (float): Value, in the range [0, 1].

      Returns:
         str: A string representing the color in hexadecimal RGB format (e.g., "#FF0000").
      """

      if applyBetterHue:
         h = self.betterHue(h)

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

if __name__ == "__main__":
   bc = betterColors()

   # Define image dimensions
   width = 512
   height = 64

   # Create a new image with RGB mode and specified dimensions
   # The 'RGB' mode means 24-bit color (8 bits per channel for Red, Green, Blue)
   image = Image.new('RGB', (width, height), color='white') # Start with a white background

   # You can now manipulate pixels or draw on the image
   # For example, draw a red square
   for x in range(width):
      for y in range(height):
         image.putpixel((x, y), bc.hsv_to_rgb_bytes(bc.betterHue(float(x)/float(width)), 1, 1)) # Set pixel to red

   # Save the image as a BMP file
   image.save("my_image.bmp")

   print("BMP image 'my_image.bmp' created successfully.")