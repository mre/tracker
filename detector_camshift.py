import cv, cv2
import numpy as np
from hand_pos import Outline, HandPos
import rectangle
from bench import benchmark
import logging

class DetectorCamshift:
  """
  Use camshift to track a hand in an image.
  This detector requires a region of interest from the image
  (the hand) to create a histogram.
  One way of doing this automatically is to use
  a HAAR detector for bootstrap.
  """

  def __init__(self, config, img, roi):
    self.config = config

    # Output shape
    self.output_shape = Outline.RECT
    # If the output shall be rectangle,
    # adjust the position a little bit.
    self.rect_offset = (0,-40)

    # Remember area in image with highest skin probabiltiy
    self.max_foreground_prob = 0

    # Create histogram from roi
    self.set_track_window(roi)
    # Run detection for inital back projection
    self.detect(img, None)

  def set_track_window(self, roi):
    # Calculate initial track window
    x0, y0, x1, y1 = roi
    width = x1 - x0
    height = y1 - y0
    if width > 0 and height > 0:
      #self.track_window = roi
      # Store region of interest for later use
      self.roi = roi
      # Track only the bottom half of the roi.
      # This empirically yields better results
      #self.track_window = (x0 + int(height/2), y0 + int(width/4), height, width - int(width/4))
      self.track_window = (x0, y0, width, height)

  def preprocess(self, img):
    """
    The preprocessing step prepares the image to improve detection probability.
    """
    self.hsv = cv2.cvtColor(img, cv2.COLOR_BGR2HSV)

  def set_mask(self, hsv):
    # Use default values...
    self.mask = cv2.inRange(hsv, np.array((0., 60., 32.)), np.array((180., 255., 255.)))
    # ...or our calculated values
    LOWER = np.array([self.config["min_hue"],
                      self.config["min_saturation"],
                      self.config["min_darkness"]],
                      np.uint8)
    UPPER = np.array([self.config["max_hue"],
                      self.config["max_saturation"],
                      self.config["max_darkness"]],
                      np.uint8)
    #self.mask = cv2.inRange(hsv, LOWER, UPPER)

  #@benchmark
  def detect(self, img, face_pos):
    """
    Track blobs with camshift
    Returns a needle hypothesis and the confidence that it is correct.
    """
    self.preprocess(img)

    x0, y0, x1, y1 = self.roi
    self.set_mask(self.hsv)

    # Extract region of interest from preprocessed image
    hsv_roi = self.hsv[y0:y1, x0:x1]
    mask_roi = self.mask[y0:y1, x0:x1]

    # Adjust histogram
    hist = cv2.calcHist( [hsv_roi], [0], mask_roi, [16], [0, 180] )
    cv2.normalize(hist, hist, 0, 255, cv2.NORM_MINMAX);
    self.hist = hist.reshape(-1)

    prob = cv2.calcBackProject([self.hsv], [0], self.hist, [0, 180], 1)
    prob &= self.mask
    term_crit = ( cv2.TERM_CRITERIA_EPS | cv2.TERM_CRITERIA_COUNT, 10, 1 )
    try:
      track_box, track_window = cv2.CamShift(prob, self.track_window, term_crit)
      self.set_track_window(track_window)
      self.get_confidence(prob, track_window)
      prob = 1 

      # Select outline (rectangle or ellipse)
      if self.output_shape == Outline.RECT:
        # Camshift normally outputs an ellipse, but if the output shall be a
        # rectangle, we can create one by creating a rectangle arround the ellipse
        # and tweaking the result.
        # Although the track window would have a rectangle shape,
        # we get much better results with the above strategy.
        position = rectangle.get_bounding_rect(track_box)
        position = rectangle.offset(position, self.rect_offset)
        return HandPos(pos=position, prob=prob, outline=Outline.RECT)
      else:
        return HandPos(pos=track_box, prob=prob, outline=Outline.ELLIPSE)
    except Exception, e:
      print e
      return HandPos()

  def get_confidence(self, prob, track_window):
    # Calculate average skin probability for background
    self.background_prob = np.average(prob)

    # Calculate average skin probability for selected foreground
    x1, y1, w,h = track_window
    x2 = x1 + w
    y2 = y1 + h
    p = prob[y1:y2,x1:x2]
    foreground_prob = np.average(p)
    if foreground_prob > self.max_foreground_prob:
      self.max_foreground_prob = foreground_prob

    # Debug
    #i = prob
    #cv2.rectangle(i, (x1, y1), (x2, y2), (255,255,255), 5)
    #cv2.imshow("Prob", i)
    #conf = foreground_prob - background_prob

    conf = foreground_prob / self.max_foreground_prob
    logging.debug("Camshift: Confidence %s", conf)
    return conf

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
