import cv, cv2
import rectangle
from numpy import concatenate
import logging

class Face(object):
  def __init__(self, config = {}):
    self.config = {
      "top_offset"      : 1.0,
      "bottom_offset"   : 1.0,
      "left_offset"     : 0.0,
      "right_offset"    : 0.0,
      "haar_confidence" : 3,
      "min_face_size"   : (70,70),
      "cascade_frontal" : "cascades/haarcascade_frontalface_default.xml",
      "cascade_profile" : "cascades/haarcascade_profileface.xml"
    }
    self.set_config(config)

    # Create the cascades. We use both, a frontal- and a profile face cascade
    self.cascade_frontal = cv2.CascadeClassifier(self.config["cascade_frontal"])
    self.cascade_profile = cv2.CascadeClassifier(self.config["cascade_profile"])

    # Initially, we have no valid face detection.
    self.face_positions = []
    # In order to improve perfomance,
    # keep the face position for a couple of frames.
    # Find face again after a certain number of frames.
    self.face_delay = 100
    # Count how many frames have passed,
    # since we last did a face detection
    self.frames_passed = 0

  def positions(self, img):
    """
    Get all faces in an  image.
    Also apply some padding to remove the area next to the faces.
    This improves both, performance and robustness of the hand search.
    """
    self.frames_passed += 1

    # Speedup. Only redetect after a certain delay.
    if self.faces_invalid():
      self.recalculate(img)
    return self.face_positions

  def faces_invalid(self):
    """
    Check if we can still use the old face positions or
    if the delay is over and we need to find the face again in the image.
    """
    if not self.face_positions:
      # No previous face detection. Declare invalid.
      return True
    if self.frames_passed > self.face_delay:
      # The delay has passed. Invalidate previous detection
      return True
    # Everything ok. We can use the old detection.
    return False

  def recalculate(self, img):
    """
    Try to redetect the face position.
    """
    logging.debug("Face detector: Scanning...")
    # Reset the frame counter
    self.frames_passed = 0
    # Invalidate previous detections
    self.face_positions = None

    rects = self.detect(img)
    for r in rects:
      x1, y1, x2, y2 = r
      logging.info("Face detector: Found face at %s", r)
    if rects != None:
      self.face_positions = rects

  def detect(self, img):
    """
    Find blobs which match a given HAAR cascade.
    """
    #gray = cv2.cvtColor(img, cv2.COLOR_BGR2GRAY)
    #gray = cv2.equalizeHist(gray)

    # Accumulate all detections in a list
    r = self.detect_frontal(img) + self.detect_profile(img)
    return r

  def detect_frontal(self, img):
    rects_frontal = self.cascade_frontal.detectMultiScale(img,
      scaleFactor=1.1,
      minNeighbors=self.config["haar_confidence"],
      minSize=self.config["min_face_size"])

    if len(rects_frontal) != 0:
      # We found a frontal faces.
      rects_frontal = rectangle.convert_from_wh(rects_frontal)
      return rects_frontal.tolist()
    else:
      return []

  def detect_profile(self, img):
    # Detect faces turned sidewards
    rects_profile = self.cascade_profile.detectMultiScale(img, 
      scaleFactor=1.2,
      minNeighbors=self.config["haar_confidence"],
      minSize=self.config["min_face_size"])

    if len(rects_profile) != 0:
      # OK, found profile faces.
      rects_profile = rectangle.convert_from_wh(rects_profile)
      return rects_profile.tolist()
    else:
      return []

  def set_config(self, config):
    """
    Load new settings at runtime
    """
    for key in config:
      self.config[key] = config[key]
