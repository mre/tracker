import cv, cv2
import rectangle
from kb_haar import HaarKB
from hand_pos import Outline, HandPos
from bench import benchmark
import logging

class DetectorHaar:
  """
  Use a HAAR cascade to find a hand in the image.
  This detector needs no warmup over many frames.
  """

  def __init__(self,
      config,
      img           = None,
      roi           = None,
      cascades      = ["cascades/1256617233-1-haarcascade_hand.xml",
                       "cascades/Hand.Cascade.1.xml"],
      confidence    = 2,
      min_hand_size = (80,80),
      max_hand_size = (500,500)):

    self.config        = config
    self.confidence    = confidence
    self.min_hand_size = min_hand_size
    self.max_hand_size = max_hand_size

    self.classifiers = []
    for c in cascades:
      self.classifiers.append(cv2.CascadeClassifier(c))

    self.kb = HaarKB(
      # Store the last few overlapping frames for further analysis
      history_length = 10,
      # Percentage of overlapping of hand position
      # in two consecutive frames
      min_overlapping = 0.5
    )

  #@benchmark
  def detect(self, img, face_pos):
    """
    Find blobs which match a given HAAR cascade.
    Returns a needle hypothesis and the confidence that it is correct.
    """

    for classifier in self.classifiers:
      rects = classifier.detectMultiScale(img, scaleFactor=1.2,
                minNeighbors=self.confidence, minSize=self.min_hand_size,
                maxSize=self.max_hand_size, flags = cv.CV_HAAR_DO_CANNY_PRUNING |cv.CV_HAAR_SCALE_IMAGE)
      if len(rects) != 0:
        # We found a result.
        # Don't run other classifier
        break

    if len(rects) == 0:
      # No classifier found a result.
      # Register an outlier.
      self.kb.update((None, face_pos))
      # Try to get a valid hand position from
      # the previous frame
      f = self.kb.get_last_frame()
      if not f:
        return HandPos()
      hand_pos, face = f
      return HandPos(pos=hand_pos)

    rects = rectangle.convert_from_wh(rects)

    if not rects.size:
      # We have not found anything.
      # Register an outlier.
      self.kb.update((None, face_pos))
      # Try to get a valid hand position from
      # the previous frame
      f = self.kb.get_last_frame()
      if not f:
        return HandPos()
      hand_pos, face = f
      return HandPos(pos=hand_pos)

    hand_pos = rectangle.max_rect(rects)

    self.kb.update((hand_pos, face_pos))

    prob = self.kb.get_confidence()
    logging.debug("Haar: Confidence %s", prob)
    return HandPos(pos=hand_pos, prob=prob, outline=Outline.RECT)

  def train(self, img):
    """
    Train the detector with a special test image. This improves the following
    detection results.
    """
    pass

  def set_config(config):
    """
    Load new settings at runtime
    """
    self.config = config

  def increase_confidence(self):
    self.confidence += 1

  def decrease_confidence(self):
    if self.confidence >= 1:
      self.confidence -= 1
