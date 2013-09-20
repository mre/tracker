"""
Arithmetic helper functions.
"""

def is_number(s):
  """
  Determine if a given input can be interpreted as a number
  This is possible for types like float, int and so on.
  """
  try:
      float(s)
      return True
  except ValueError:
      return False
