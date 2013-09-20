import cv2
import rectangle
from hand_pos import Outline, HandPos
from bench import benchmark
import numpy as np
import logging

class DetectorShape:
  """
  A detector which matches a given shape (needle) to a part of a larger image (haystack).
  This detector needs no warmup over many frames; just a single
  image -- called template -- which will be the shape to search for.
  """

  def __init__(self, config, img = None, roi = None, match_method = cv2.TM_CCOEFF):
    self.config = config
    self.match_method = match_method
    if img != None and roi != None:
      # Create template from given image
      self.create_template(img, roi)
    else:
      # Load a default template
      self.set_template(cv2.imread("assets/hand2.jpg"))

  def create_template(self, img, roi):
    """
    Create a template image to match
    """
    x0, y0, x1, y1 = roi
    # Copy template region to new image
    template = img[y0:y1, x0:x1]
    # Consider only red channel for template matching
    template = template[:,:,2]
    # Remove noise
    template = template - cv2.erode(template, None)
    #template = cv2.GaussianBlur(template,(3,3),0)
    self.set_template(template)

  def set_template(self, template):
    """
    Set template image (needle), which we will search in the video capture
    (haystack)
    """
    self.templ = template
    # Precalculate template size
    self.templ_w, self.templ_h = self.templ.shape[:2]

  def preprocess(self, img):
    """
    The preprocessing step prepares the image to improve detection probability.
    """
    # Make a copy of the image
    self.img = img.copy()
    # Consider only red channel for template matching
    self.img = self.img[:,:,2]
    # Remove noise
    #self.img = cv2.GaussianBlur(self.img,(3,3),0)
    self.img = self.img - cv2.erode(self.img, None)

  #@benchmark
  def detect(self, img, face_pos):
    """
    Returns a needle hypothesis and the confidence that it is correct.
    """
    # Do the Matching and Normalize

    self.preprocess(img)

    self.result = cv2.matchTemplate(self.img, self.templ, self.match_method)
    cv2.normalize(self.result, self.result, 0, 1, cv2.NORM_MINMAX)

    # Localizing the best match with minMaxLoc
    self.minVal, self.maxVal, self.minLoc, self.maxLoc = cv2.minMaxLoc(self.result)

    # For SQDIFF and SQDIFF_NORMED, the best matches are lower values. For all the other methods, the higher the better
    if self.match_method  == cv2.TM_SQDIFF or self.match_method == cv2.TM_SQDIFF_NORMED:
      self.matchLoc = self.minLoc
      #loc = np.where(result == result.min())
    else:
      self.matchLoc = self.maxLoc
      #loc = np.where(result == result.max())

    # Create a rectangle containing the hand
    x1 = self.matchLoc[0]
    y1 = self.matchLoc[1]
    x2 = x1 + self.templ_h
    y2 = y1 + self.templ_w

    #for pt in zip(*loc[::-1]):
    #  if result[pt[::-1]] < 0.4:
    #    continue

    needle_rect = [x1, y1, x2, y2]

    prob = self.get_confidence()

    return HandPos(pos=needle_rect, prob=prob)

  def get_confidence(self):
    """
    Probabilty to for correct hand position.
    """
    median = np.median(self.result)
    #logging.debug("Shape: Median %s", median)
    #logging.debug("Shape: Min %s Max %s", self.minVal, self.maxVal)
    conf = (self.maxVal - median)/(self.maxVal)
    logging.debug("Shape: Confidence %s", conf)
    return conf

  def train(self, img):
    """
    Train the detector with a special test image. This improves the subsequent
    detection results.
    """
    pass

  def set_config(config):
    """
    Load new settings at runtime
    """
    self.config = config
