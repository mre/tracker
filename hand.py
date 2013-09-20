class Hand(object):
  """
  Store all hand properties (position, shape) inside an object.
  """
  def __init__(self, features = {}):
    defaults = {
      "contour"         : None,  # Outer hand contour
      "contours"        : None,  # All hand contours
      "contours_offset" : (0,0), # Offset for contours in image (used for drawing)
      "hierarchy"       : None,  # Hierarchy of contours
      "area"            : 0,     # Hand area in image
      "hull"            : 0,     # Convex hulls from contours recognized in image
      "fingers"         : [],    # Lines to highlight fingers in contours
      "num_fingers"     : 0,     # Fingers shown
      "positions"       : {}     # Dict of hand positions as reported by the detectors
    }

    # Set default config
    for key in defaults:
      setattr(self, key, defaults[key])

    # Modify with available parameters
    for key in features:
      setattr(self, key, features[key])

if __name__ == "__main__":
  # TEST
  features = {"contour": [12]}
  h = Hand(features)
  print h.contour
  print h.hull
