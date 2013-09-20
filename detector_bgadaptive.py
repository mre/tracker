import cv, cv2
import rectangle
from hand import Hand
import numpy as np
import geom
from bench import benchmark

class DetectorAdaptive:
  """
  Hand extraction using background subtraction
  """

  def __init__(self, config, img, roi):
    self.config = config
    self.roi = roi

    history = 500 
    nGauss = 2 
    bgThresh = 0.01 
    noise = 1 
    self.mog = cv2.BackgroundSubtractorMOG(history,nGauss,bgThresh,noise)

    # Minimum and maximum angles between two fingers
    self.min_finger_angle = 10
    self.max_finger_angle = 90

    # Minimum and maximum length of finger
    self.min_finger_len = 10
    self.max_finger_len = 100

    # The tip of a finger must be above the palm
    # (or slightly below, when it comes to the thumb)
    self.finger_orientation_thresh = -20

  def crop(self, img, roi):
    """
    Crop an image
    """
    x1, y1, x2, y2 = roi
    # Remember the location of the
    # cropped region in the image
    self.offset = (x1, y1)
    return img[y1:y2,x1:x2]

  def preprocess(self, img, roi):
    """
    The preprocessing step prepares the image to improve detection probability.
    """
    #img = self.crop(img, roi)
    # TODO: Try adaptive threshold
    img = cv2.cvtColor(img, cv2.COLOR_BGR2GRAY)
    return img

  #@benchmark
  def detect(self, img, roi):
    """
    Find hand object (fingers, contours) in region of interest
    """
    # Only consider region of interest
    img = self.preprocess(img, roi)

    background = self.mog.apply(img)
    cv2.imshow("BG", background)
    cv2.waitKey(300)
    return background

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

