"""
Primitives to draw on images using OpenCV
"""

import cv2

def draw_contours(img, contours, hierarchy, color, opacity=1, offset = (0,0)):
  """
  Draw contours on an image with a given opacity
  """
  if not contours:
    return
  overlay = img.copy()
  #cv2.drawContours(overlay,contours,-1, color,-1)
  cv2.drawContours(overlay,contours,-1, color,-1, 8, hierarchy, 1, offset)
  cv2.addWeighted(overlay, opacity, img, 1 - opacity, 0, img)

def draw_contour(img, contour, color, opacity=1, offset = (0,0)):
  """
  Draw a single contour on an image with a given opacity
  """
  if not contour:
    return
  overlay = img.copy()
  cv2.drawContours(overlay,contour,-1, color,-1, 8, None, 1, offset)
  #cv2.drawContours(overlay,contours,-1, color,-1, 8, hierarchy, 1, offset)
  cv2.addWeighted(overlay, opacity, img, 1 - opacity, 0, img)

def cross(img, point, color=(0,0,255), thickness=5, delta=20):
  """
  Draw a cross on an image to mark a point.
  """
  x, y = point
  # Horizontal line
  start = (x - delta, y)
  end = (x + delta, y)
  cv2.line(img, start, end, color, thickness)
  # Vertical line
  start = (x, y - delta)
  end = (x, y + delta)
  cv2.line(img, start, end, color, thickness)

def draw_lines(img, lines, color):
  """
  Draw a bunch of lines on an image
  """
  for (start, end) in lines:
    cv2.line(img, start, end, color, 5)

def draw_rect(img, rect, color, thickness=2):
  """
  Draw a rectangle onto an image
  """
  x1, y1, x2, y2 = rect
  cv2.rectangle(img, (x1, y1), (x2, y2), color, thickness)

def color_gradient(x, maxval=255):
  """
  Return a color value between red and green depending on x.
  """
  r = -maxval * x + maxval
  g = maxval * x
  color = (0, g, r)
  return color
