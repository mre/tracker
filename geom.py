"""
Geometrical helper functions
"""

from numpy import sqrt, arccos, rad2deg

def distance(p1, p2):
    """
    Calculate the euclidian distance between two points
    """
    x = abs(p1[0] - p2[0])
    y = abs(p1[1] - p2[1])
    d = sqrt(x**2+y**2)
    return d

def angle(cent, line1, line2):
  """
  Calculate the angle between two lines
  """
  v1 = (line1[0] - cent[0], line1[1] - cent[1])
  v2 = (line2[0] - cent[0], line2[1] - cent[1])
  dist = lambda a:sqrt(a[0] ** 2 + a[1] ** 2)
  angle = arccos((sum(map(lambda a, b:a*b, v1, v2))) / (dist(v1) * dist(v2)))
  angle = rad2deg(angle)
  return angle
