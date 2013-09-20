import rectangle

class HaarKB(object):
  """
  Knowledge base for HAAR detector.
  Only collect information for this specific detector here.
  """
  def __init__(self, history_length = 10, min_overlapping = 0.7):
    # The history is a simple sequence of frames
    self.history = []
    self.max_history = history_length
    self.min_overlapping = min_overlapping

  def update(self, frame):
    """
    Store new frame and make sanity checks.
    """
    self.add_frame(frame)

    if self.too_many_outliers() or not self.overlapping():
      self.reset()

  def overlapping(self):
    """
    Subsequent hand positions must overlap by a certain percentage
    in order to be valid.
    """
    # Check if the history is long enough for further analysis
    if len(self.history) < 3:
      return True

    current = self.history[-1]
    father = self.history[-2]

    if current == None or father == None:
      return True

    # Unpack the hand from the frames
    current_hand, current_face = current
    father_hand, father_face   = father

    overlapping = rectangle.intersect_percentage(current_hand, father_hand)
    return overlapping >= self.min_overlapping

  def too_many_outliers(self):
    """
    Two subsequent frames may not be invalid
    """
    # Check if the history is long enough for further analysis
    if len(self.history) < 2:
      return False
    # Frames must intersect by a certain percentage to
    # be valid. Only one outlier is allowed.
    current = self.history[-1]
    father = self.history[-2]
    # Check if we have more than one outlier
    return current == None and father == None

  def get_last_frame(self):
    """
    Returns the last frame from history.
    This can be useful if something goes
    wrong with the current detection.
    """
    if len(self.history) < 1:
      return None
    return self.history[-1]

  def add_frame(self, frame):
    """
    Store frame in knowledge base
    """
    self.history.append(frame)
    # Only keep the last few frames
    self.history = self.history[-self.max_history:]

  def conf_face_detect(self):
    """
    Calculate the quota of face detections in history
    """
    if len(self.history) == 0:
      return 0.0

    f = self.faces_found() / float(len(self.history))
    return f

  def faces_found(self):
    """
    Count the number of detected faces in the
    frame history.
    """
    num_faces = sum([1 for (h,f) in self.history if f])
    return num_faces

  def conf_hand_detect(self):
    """
    The longer the number of frames in the history, the better
    is the detection process.
    """
    return len(self.history) / float(self.max_history)

  def get_confidence(self):
    """
    Determine the confidence by a number
    of influential factors which are
    - number of consecutive overlapping frames.
    - faces found during history
    Basically, the confidence should be high, if we have
    a consistent result over many frames.
    """

    # Hand may not be much smaller or bigger than face
    # TODO: Implement heuristic properly
    #x1, y1, x2, y2 = hand_pos
    #hand_size = (x2-x1)*(y2-y1)

    conf = self.conf_hand_detect()
    f = self.conf_face_detect()


    """
    TODO: Make a predicate out of this condition
    If no faces are detected during history, the probability for a correct detection
    is pretty high (No user is facing the camera).
    If a face is constantly found over many frames, the probability is also high.
    Problems arise, when a face is detected irregularly. Then, we adjust the
    probabilty for a correct hand detection based on the graph below.

        delta
         ^
      0.5| _________
         | |        \
         | |         \
         | |          \
         ----------------------> num_faces / history_length
         0 0.1   0.5   1.0
    """

    if f < 0.1:
      delta = 0.0
    elif f < 0.5:
      delta = 0.5
    else:
      delta = -f + 1
    conf = conf - delta

    return max([0, conf])

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
