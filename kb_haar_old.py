import rectangle

class HaarKB(object):
  def __init__(self, history_length = 10, min_overlapping = 0.5):
    # The history is a simple sequence of frames
    self.history = []
    self.history_length = history_length
    self.min_overlapping = min_overlapping

  def update(self, frame):
    self.add_frame(frame)

    if self.too_many_outliers() or not self.overlapping():
      self.reset()

  def faces_found(self):
    """
    Count the number of detected faces in the
    frame history.
    """
    num_faces = sum([1 for (h,f) in self.history if f])
    return num_faces

  def overlapping(self):
    if len(self.history) < 2:
      return True

    current = self.history[-1] # Last frame
    father = self.history[-2] # Second to last frame

    if current == None or father == None:
      return True

    # Unpack the hand from the frames
    current_hand, current_face = current
    father_hand, father_face   = father


    overlapping = rectangle.intersect_percentage(current_hand, father_hand)
    return overlapping >= self.min_overlapping

  def too_many_outliers(self):
    # Check if the history is long enough for further analysis
    if len(self.history) < 2:
      return False

    # Frames must intersect by a certain percentage to
    # be valid. Only one outlier is allowed.
    current = self.history[-1]
    father = self.history[-2]

    # Say if we have more than one outlier
    return current == None and father == None

  def add_frame(self, frame):
    # Store the frame in knowledge base
    self.history.append(frame)
    # Only keep the last few frames
    self.history = self.history[-self.history_length:]

  def conf_face_detect(self):
    f = self.faces_found()

  def conf_hand_detect(self):
    return len(self.history) / float(self.history_length)

  def get_confidence(self):
    """
    Determine the confidence by a number
    of influential factors which are
    - number of consecutive overlapping frames.
    - faces found found during history
    Basically, the confidence should be high, if we have
    a consistent result over many frames.
    """

    # TODO: WEIGHTED AVERAGE
    conf = self.conf_hand_detect()
    return conf

  def reset(self):
    self.history = []

if __name__ == "__main__":
  # Test
  kb = KnowledgeBase()
  kb.update(1)
  kb.update(1)
  kb.update(None)
  kb.update(None)
  print kb.get_confidence()
