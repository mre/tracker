class Outline(object):
  """
  Outline of hand detection.
  """
  RECT    = 1
  ELLIPSE = 2

class HandPos(object):
  """
  Each position detector returns a HandPos object,
  with the following fields:
  - detector_name - The name of the filter which was used
  - rect - The position of the hand represented as a rectangle
  - prob - The probabilty that the position is correct
  """
  def __init__(self, **kwargs):
    defaults = {
      "pos"     : None,
      "prob"    : 0.0,
      "outline" : Outline.RECT,
    }

    # Set default config
    for key in defaults:
      setattr(self, key, defaults[key])

    # Modify with available parameters
    for key in kwargs:
      setattr(self, key, kwargs[key])

if __name__ == "__main__":
  # TEST
  h = HandPos(outline=Outline.ELLIPSE)
  print h.outline
  print h.prob
  h = HandPos()
  print h.outline
  print h.prob
