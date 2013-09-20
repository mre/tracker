import cv, cv2
import rectangle
from hand import Hand
import numpy as np
import geom
from bench import benchmark
import logging

class DetectorSkin:
  """
  Hand extraction using HSV based skin detection.
  """

  def __init__(self, config, img, roi):
    self.config = config
    """
    self.kb = SkinKB(
      # Store the last few overlapping frames for further analysis
      history_length = 10,
      # Percentage of overlapping of hand position
      # in two consecutive frames
      min_overlapping = 0.5
    )
    """
    self.roi = roi

    # Minimum and maximum angles between two fingers
    self.min_finger_angle = 10
    self.max_finger_angle = 90

    # Minimum and maximum length of finger
    self.min_finger_len = 10
    self.max_finger_len = 100

    # The tip of a finger must be above the palm
    # (or slightly below, when it comes to the thumb)
    self.finger_orientation_thresh = -20

  def filter_skin(self, hsv):
    # Use default values...
    #filter_im = cv2.inRange(hsv, np.array((0., 60., 32.)), np.array((180., 255., 255.)))
    # ...or our calculated values
    LOWER = np.array([self.config["min_hue"],
                      self.config["min_saturation"],
                      self.config["min_darkness"]],
                      np.uint8)
    UPPER = np.array([self.config["max_hue"],
                      self.config["max_saturation"],
                      self.config["max_darkness"]],
                      np.uint8)
    filter_im = cv2.inRange(hsv, LOWER, UPPER)
    return filter_im

  def remove_noise(self, contours_img):
    """
    Improve contours image for better postprocessing
    """
    # Smooth to get rid of some false positives
    if self.config["smooth"] > 0:
      contours_img = cv2.blur(contours_img, (self.config["smooth"], self.config["smooth"]))
    # Emphasize contours
    if self.config["erode"] > 0:
      contours_img = cv2.erode(contours_img, 
                  cv2.getStructuringElement(cv2.MORPH_ELLIPSE,
                  (self.config["erode"], self.config["erode"])))
    if self.config["dilate"] > 0:
      contours_img = cv2.dilate(contours_img, 
                  cv2.getStructuringElement(cv2.MORPH_ELLIPSE,
                  (self.config["dilate"], self.config["dilate"])))
    return contours_img

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
    img = self.crop(img, roi)
    # Set image proportions
    self.img_width, self.img_height = img.shape[:2]

    # Convert to hsv
    hsv = cv2.cvtColor(img, cv2.COLOR_BGR2HSV)

    # Get skin and improve result
    filtered = self.filter_skin(hsv)
    filtered = self.remove_noise(filtered)
    #cv2.imshow("Skin", filtered)
    return filtered

  #@benchmark
  def detect(self, img, roi):
    """
    Find hand object (fingers, contours) in region of interest
    """
    try:
      # Only consider region of interest
      img = self.preprocess(img, roi)
      # Detect hand contour
      contours, hierarchy = self.get_contours_approx(img)
      hand_cnt, hand_area = self.get_max_contour(contours)

      # Calculate defects of convex hull which are interpreted as fingers
      fingers = []
      if hand_cnt != None:
        hand_hull = cv2.convexHull(hand_cnt,returnPoints = False)
        defects = self.get_defects(hand_cnt, hand_hull)

        fingers = self.get_fingers(hand_cnt, defects)

      return Hand({
        "contours"        : contours,
        "contour"         : hand_cnt,
        "contours_offset" : self.offset,
        "area"            : hand_area,
        "hierarchy"       : hierarchy,
        "fingers"         : fingers,
        "num_fingers"    : len(fingers) +1 # Add one for missing last finger line
      })
    except Exception, e:
      logging.exception("Skin: Error finding contours")
      return Hand()

  def get_fingers(self, hand_cnt, defects):
    """
    Analyze the convexity defects and extract finger information
    """
    fingers = [] # Lines from the tip of a finger to the palm
    for i in range(defects.shape[0]):
      defect = defects[i,0]
      finger = self.get_finger(hand_cnt, defect)
      if finger:
        fingers.append(finger)
    return fingers

  def get_finger(self, hand_cnt, defect):
    """
    Calculate the two lines from the tip to the bottom of a finger
    from a given convexity defect.
    """
    finger_lines = []
    if self.is_finger(hand_cnt, defect):
      offset = self.offset
      s, e, f, d = self.get_finger_points(hand_cnt, defect)
      start = (s[0] + offset[0], s[1] + offset[1])
      far   = (f[0] + offset[0], f[1] + offset[1])
      end   = (e[0] + offset[0], e[1] + offset[1])
      finger_lines = [(start, far), (far, end)]
    return finger_lines

  def is_finger(self, hand_cnt, defect):
    # Check proportions of potential finger
    if not self.valid_finger_length(defect):
      return False
    # Check finger orientation
    if not self.valid_finger_orientation(hand_cnt, defect):
      return False
    # Check angles between fingers
    if not self.valid_angle(hand_cnt, defect):
      return False
    return True

  def get_finger_points(self, hand_cnt, defect):
    """
    Extract the four elements of a convexity defect. These are
    start_index, end_index, farthest_pt_index, fixpt_depth
    """
    s, e, f, depth = defect
    start = tuple(hand_cnt[s][0])
    end = tuple(hand_cnt[e][0])
    far = tuple(hand_cnt[f][0])
    return start, end, far, depth

  def get_contours_approx(self, img):
    """
    Get an approximation of the contours of an image
    """
    contours, hierarchy = cv2.findContours(img, cv2.RETR_TREE, cv2.CHAIN_APPROX_SIMPLE)
    for cnt in contours:
      # Approximate even more
      cnt = cv2.approxPolyDP(cnt,0.1*cv2.arcLength(cnt,True),True)
    return contours, hierarchy

  def get_defects(self, cnt, hull):
    """
    Get convexity defects from a contour.
    """
    if len(cnt) > 3:
      return cv2.convexityDefects(cnt, hull)
    else:
      return None

  def get_max_contour(self, contours):
    """
    Get the contour with the biggest area 
    from a list of contours.
    """
    max_cnt = None
    max_area = 0
    for cnt in contours:
        area = cv2.contourArea(cnt)
        if area > max_area:
          max_area = area
          max_cnt = cnt
    return max_cnt, max_area

  def valid_finger_length(self, defect):
    """
    Sanity check:
    Check if the hull defect is big enough to be a finger.
    Compare the finger length to the overall length of the search window.
    If the finger is within a certain ratio, it is considered to be "valid".
    """
    # Get the floating-point value of the depth
    start, end, far, depth = defect
    proportion = (depth / float(self.img_width))
    return self.min_finger_len < proportion < self.max_finger_len

  def valid_angle(self, hand_cnt, defect):
    """
    Sanity check:
    Angles within a certain range count as fingers
    """
    start, end, far, depth = self.get_finger_points(hand_cnt, defect)
    a = geom.angle(far, start, end)
    return self.min_finger_angle < a < self.max_finger_angle

  def valid_finger_orientation(self, hand_cnt, defect):
    """
    Sanity check:
    The hand is properly orientated if the tip of the finger
    is above the point closest to the palm
    (or just slightly below for the thumb).
    """
    start, end, far, depth = self.get_finger_points(hand_cnt, defect)
    return (far[1] - start[1] > self.finger_orientation_thresh) and \
           (far[1] - end[1]   > self.finger_orientation_thresh)

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
