"""
A collection of rectangle helper functions
"""

import itertools
from collections import namedtuple

def all_intersect(rectangles):
  """
  Check if all rectangles in the container intersect.
  """
  pairs = itertools.combinations(rectangles, 2)
  for r1,r2 in pairs:
    if separate(r1, r2):
      return False
  return True

def separate(r1, r2):
  """
  Check if two rectangles don't intersect.
  """
  return not intersect(r1, r2) and not contains(r1, r2) and not contains(r2, r1)

def intersect(r1, r2):
  """
  Check if two rectangles intersect.
  """
  r1_left, r1_top, r1_right, r1_bottom = r1
  r2_left, r2_top, r2_right, r2_bottom = r2

  separate = r1_right < r2_left or \
    r1_left > r2_right or \
    r1_top > r2_bottom or \
    r1_bottom < r2_top
  return not separate

def contains(r1, r2):
  """
  Check, if rectangle 1 fully contains rectangle 2.
  """
  r1_left, r1_top, r1_right, r1_bottom = r1
  r2_left, r2_top, r2_right, r2_bottom = r2
  return r1_right >= r2_right and  r1_left <= r2_left and  r1_top <= r2_top and  r1_bottom >= r2_bottom

def adjacent_pairs(seq):
  it = iter(seq)
  a = it.next()
  for b in it:
      yield a, b
      a = b

def avg_dimensions(positions):
  widths = [x2-x1 for x1, _, x2, _ in positions]
  width = sum(widths) / len(widths)

  heights = [y2-y1 for _, y1, _, y2 in positions]
  height = sum(heights) / len(heights)

  return width, height

def center(rect):
  """
  Calculate the center of a rectangle
  """
  x1, y1, x2, y2 = rect
  w = x2 - x1
  h = y2 - y1
  cx = x1 + w/2
  cy = y1 + h/2
  return (cx, cy)

def median_center(positions):
  centers_x = sorted([(x2+x1)/2 for x1, _, x2, _ in positions])
  center_x = centers_x[len(centers_x)//2]

  centers_y = sorted([(y2+y1)/2 for _, y1, _, y2 in positions])
  center_y = centers_y[len(centers_y)/2]

  Point = namedtuple("Point", "x y")
  return Point(center_x, center_y)

def get_rect(dim, center):
  """ Create a rectangle out of a given dimension and a center point """
  width, height = dim
  dx = width / 2
  dy = height / 2
  return [center.x - dx, center.y - dy, center.x + dx, center.y + dy]

def max_rect(rects):
  rects_width = [rect[2] - rect[0] for rect in rects]
  max_value = max(rects_width)
  max_index = rects_width.index(max_value)
  return rects[max_index]

def min_rect(rects):
  rects_width = [rect[2] - rect[0] for rect in rects]
  min_value = min(rects_width)
  min_index = rects_width.index(min_value)
  return rects[min_index]

def intersect(r1, r2):
  """ Calculate intersection between two rectangles """
  if r1 == None or r2 == None:
    return None

  x11, y11, x12, y12 = r1
  x21, y21, x22, y22 = r2

  left   = max(x11, x21)
  right  = min(x12, x22)
  top    = max(y11, y21)
  bottom = min(y12, y22)

  if left < right and top < bottom:
      return [left, top, right, bottom]
  else:
      return None

def intersect_percentage(r1, r2):
  i = intersect(r1, r2)
  if i == None or r1 == None or r2 == None:
    return 0.0

  # Force floating point division.
  # This is the standard behavior in Python 3,
  # but not Python 2.x
  # See http://stackoverflow.com/questions/1267869/how-can-i-force-division-to-be-floating-point-in-python
  percentage = area(i) / float(area(r1))
  return percentage

def area(r):
  x1, y1, x2, y2 = r
  width = x2 - x1
  height = y2 - y1
  return width * height

def resize(r, percentage):
  x1, y1, x2, y2 = r
  width = (x2 - x1)
  height = (y2 - y1)
  center_x = x1 + width / 2
  center_y = y1 + height / 2
  new_width = width * percentage
  new_height = height * percentage
  dx = new_width / 2
  dy = new_height / 2
  x1 = max(0, int(center_x - dx))
  x2 = int(center_x + dx)
  y1 = max(0, int(center_y - dy))
  y2 = int(center_y + dy)
  return [x1, y1, x2, y2]

def offset(r, offs):
  """
  Move rectangle
  """
  x1, y1, x2, y2 = r
  dx, dy = offs
  r = [x1 + dx, y1 + dy, x2 + dx, y2 + dy]
  # Remove negative values (if any)
  return [max(0, coord) for coord in r]

def get_bounding_rect(ellipse):
  center, axes, angle = ellipse
  center = (int(center[0]), int(center[1]))
  rad = int(axes[1] / 2)
  rect = [center[0] - rad, center[1] - rad, center[0] + rad, center[1] + rad]
  return rect

def convert_from_wh(rect):
  """
  Convert the format of a rectangle from
  rect = [x, y, width, height]
  to
  rect = [x1, y1, x2, y2]
  """
  rect[:,2:] += rect[:,:2]
  return rect
