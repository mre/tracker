class KB(object):
  """
  Knowledge base for all detectors.
  """
  def __init__(self, history_length = 10):
    # The history is a simple sequence of frames
    KB.history = []
    self.max_history = history_length

  def update(self, frame):
    """
    Store frame in knowledge base
    """
    KB.history.append(frame)
    # Only keep the last few frames
    KB.history = KB.history[-self.max_history:]

  def reset(self):
    KB.history = []
