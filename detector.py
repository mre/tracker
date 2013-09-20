from collections import namedtuple
from itertools import combinations
import logging

from face import Face
from hand import Hand
from hand_pos import Outline, HandPos
import rectangle
import predict
import draw # TODO: REMOVE
import cv2 # TODO: REMOVE

# Detectors
from detector_haar import DetectorHaar
from detector_camshift import DetectorCamshift
from detector_shape import DetectorShape
from detector_skin import DetectorSkin
from detector_bgadaptive import DetectorAdaptive

class DetectorType(object):
  """
  There are two types of detectors:
  One detects the hand position, the other detects hand features (like the
  shape)
  """
  POS  = 1
  HAND = 2

class Detector:
  """
  Detector is a cascade of detectors (image filters) which can extract
  a hand position and its features (such as the number of fingers) from an
  input image. The system is adapting to the input and gets better over time.

  The cascade consists of two different kinds of detectors, position and
  feature detectors.

  Each position detector calculates an estimated hand position and a probability
  that the estimation is correct.
  The combination (weighted by the probability) of all estimated hand positions
  gets used to predict a more accurate hand position.

  Afterwards the properties of a hand object will be determined by the feature
  detectors.
  """
  def __init__(self, config):
    self.config = config

    # Face detector
    self.remove_faces = False
    self.face = Face(self.config)

    """
    Detectors for hand and hand position.
    use: Each detector can be enabled and disabled with this flag
    constructor: Constructor which will be called to create the detector instance
    deps: Detectors depend on other detectors.
          All dependencies must be satisfied in order to start a detector
    instance: Holds the instance after the constructor was called
    """
    # Name { Parameters }
    self.detectors = {
      # Position detectors
      "haar": {"type": DetectorType.POS,
               "use": True,
               "constructor": "DetectorHaar",
               "deps" : [],
               "instance": None},

      "camshift": {"type": DetectorType.POS,
               "use": False,
               "constructor": "DetectorCamshift",
               "deps" : ["haar"],
               "instance": None},

      "shape": {"type": DetectorType.POS,
               "use": True,
               "constructor": "DetectorShape",
               "deps" : ["haar"],
               "instance": None},

      # Hand detectors
      "skin": {"type": DetectorType.HAND,
               "use": True,
               "constructor": "DetectorSkin",
               "deps" : ["haar"],
               "instance": None},

      "bg":  {"type": DetectorType.HAND,
               "use": False,
               "constructor": "DetectorAdaptive",
               "deps" : ["haar"],
               "instance": None}
    }

    # Bootsrapping a detector is only allowed when the
    # detectors it depends on has a high detection probability
    self.min_bootstrap_prob = 0.9

    # There is no initial prediction for the hand position
    # since the detectors didn't run yet.
    self.positions = {"estimate": HandPos()}

  def detect(self, img):
    """
    Detects state of hand (position and fingers).
    """
    # Work on a copy of the original image
    # to prevent the user from seeing temporary image modifications
    # (i.e. face removal)
    self.current_img = img.copy()
    self.preprocess()
    self.positions = self.get_hand_pos()

    hand = self.get_hand()
    return hand

  def get_hand_pos(self):
    """
    Returns a hand position hypothesis and the confidence that it is correct.
    If training of detector is not yet completed, return a confidence of 0.
    Returns none if no hand position was found.
    """
    positions = self.run_detectors(DetectorType.POS)
    positions["estimate"] = self.predict(positions)
    return positions

  def get_hand(self):
    """
    Returns the properties of a hand at the given position.
    This will only work, if the position for the hand is correct.
    """
    hands = self.run_detectors(DetectorType.HAND)
    if hands:
      hand = hands["skin"]
    else:
      hand = Hand()

    hand.pos = self.positions
    return hand

  def run_detectors(self, detector_type):
    """
    Run all detectors of a certain type
    """
    results = {}
    for detector_name, parameters in self.detectors.iteritems():
      # Check if detector is of the correct type and should be used
      if parameters["use"] and parameters["type"] == detector_type:
        try:
          result = self.run_detector(detector_name, parameters)
          if result:
            results[detector_name] = result
        except Exception, e:
          logging.exception("Detector: Problem running detector")
    return results

  def predict(self, positions):
    """
    Predict the correct hand position from all detector inputs.
    """
    # Check if overlapping
    overlapping = predict.positions_overlap(positions)
    if len(overlapping) > 1:
      # Calculate a weighted average rectangle over all
      # overlapping rectangles
      h = predict.average_weighted(overlapping)
      if h.prob > 0.5:
        return h
    # Not overlapping.
    # Fall back to rect with highest probability
    return predict.max_prob(positions)

  def run_detector(self, detector_name, parameters):
    """
    Runs a single detector
    """
    if self.detector_running(detector_name):
      detector = parameters["instance"]
      # Check detector type and pass all necessary parameters
      if parameters["type"] == DetectorType.POS:
        return detector.detect(self.current_img, self.face_positions)
      else:
        # Contrary to position detectors, hand detectors
        # need a region of interest to detect hand features
        return detector.detect(self.current_img, self.positions["estimate"].pos)

    # Detector not running yet. Can we start?
    if parameters["use"] and self.deps_satisfied(detector_name):
      logging.info("Bootstrapping %s", detector_name)
      self.bootstrap_detector(parameters)
    return None

  def train(self, img):
    """
    Train the detector with a special test image. This improves the following
    detection results.
    The test image is certain to contain a hand with the following properties:
    - All five fingers are visible
    - The hand is upright and directly in front of the camera
    - If the user is right-handed, the hand will probably be on the right side.
    - If the user is left-handed, the hand will probably be on the left side.

    Adjust the parameters of the detector to find the hand in the given image
    and return a confidence that the position is correct.
    """
    pass

  def preprocess(self):
    """
    Remove all faces from image for better hand detection
    """
    if self.remove_faces:
      self.face_positions = self.face.positions(self.current_img)
      for f in self.face_positions:
        x1, y1, x2, y2 = f
        #width = x2-x1
        #x1 = int(x1 + width/4)
        #x2 = int(x2 - width/4)
        self.current_img[y1:y2,x1:x2] = 0
    else:
      self.face_positions = None

  def deps_satisfied(self, detector_name):
    """
    Check if all dependencies are satisfied to bootstrap the detector
    """
    parameters = self.detectors[detector_name]
    for dep_name in parameters["deps"]:
      if not self.detector_running(dep_name) or \
         not self.detector_stable(dep_name):
        return False
    return True

  def detector_stable(self, detector_name):
    """
    Check if a detector delivers satisfying results to bootstrap
    other detectors with its current output.
    """
    parameters = self.positions.get(detector_name, None)
    if parameters and parameters.prob > self.min_bootstrap_prob:
      return True
    return False

  def detector_running(self, detector_name):
    """
    Check if the detector is currently running.
    """
    parameters = self.detectors[detector_name]
    return parameters["instance"] != None

  def bootstrap_detector(self, parameters):
    """
    Start a detector with input data (hand position)
    from other detectors.
    """
    detector_name = parameters["constructor"]
    detector = globals()[detector_name]

    pos = self.positions["estimate"].pos

    # Store instance of detector for later calls
    parameters["instance"] = detector(self.config, self.current_img, pos)

  def set_config(config):
    """
    New settings have been loaded.
    Adjust the settings for each detector at runtime.
    """
    for detector_name, parameters in self.detectors.iteritems():
      detector = parameters["instance"]
      detector.set_config(config)

  def reset(self):
    """
    Something went very wrong. Remove all detector instances and start anew.
    This also clears the history.
    """
    for detector_name, parameters in self.detectors.iteritems():
      parameters["instance"] = None
