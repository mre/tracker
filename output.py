import cv2
import datetime

import draw
from hand import Hand
from hand_pos import Outline, HandPos
import logging

class Output(object):
  def __init__(self, **kwargs):
    defaults = {
      # Show estimated hand position in final output
      "show_estimate": False,
      # Show detector results in final output
      "show_detectors": True,
      # Show skin contours in final output
      "show_skin": True,
      # Colorful output
      "rainbow_colors": False,
      # Store screenshots in separate directory
      "screenshot_dir": "assets/screenshots/"
    }

    # Set default config
    for key in defaults:
      setattr(self, key, defaults[key])

    # Modify with available parameters
    for key in kwargs:
      setattr(self, key, kwargs[key])

    # Some colors for drawing
    self.colors = {
      "white"    : (255,255,255),
      "blue"     : (233, 183, 47),
      "darkblue" : (183, 72, 37),
      "green"    : (0,182,136),
      "yellow"   : (0,255,255),
      "red"      : (67,47,241)
    }

    self.output_settings = {
      # Detector: (color, thickness)
      "estimate": (self.colors["white"] , 8),
      "haar": (self.colors["green"]     , 4),
      "camshift": (self.colors["red"]   , 4),
      "shape": (self.colors["blue"]     , 4),
      "default": (self.colors["yellow"] , 4)
    }

  def show(self, img, hand, reference_point = None):
    """
    Create output with transparent image overlay
    """
    # Store current image
    self.img = img

    # Output
    self.output_positions(hand)
    self.output_hand_contour(hand)
    self.output_reference_point(reference_point)
    cv2.imshow("Tracker", self.img)

  def output_reference_point(self, ref):
    """
    Draw the reference point for mouse movement
    """
    if ref: draw.cross(self.img, ref)

  def output_positions(self, hand):
    """
    Draw hand estimates of all running detectors
    """
    for detector, properties in hand.pos.iteritems():
      if detector == "estimate":
        if not self.show_estimate:
          continue
      elif not self.show_detectors:
        continue
      color, thickness = self.get_output_settings(detector, properties)
      if properties:
        self.draw_shape(properties.pos, properties.outline, color, thickness)

  def output_hand_contour(self, hand):
    """
    Draw a hand contour on the image
    """
    if self.show_skin:
      self.draw_hand(hand)

  def get_output_settings(self, detector, properties):
    """
    Specify color and thickness of geometric shape for detector output.
    """
    if detector == "estimate":
      return self.output_settings["estimate"]

    if self.rainbow_colors:
      return self.output_settings[detector]
    else:
      return (draw.color_gradient(properties.prob), 4)

  def draw_shape(self,pos, outline, color, thickness):
    """
    Draw a geometric shape above the image
    """
    if pos == None:
      return
    try:
      if outline == Outline.RECT:
        draw.draw_rect(self.img, pos, color, thickness)
      elif outline == Outline.ELLIPSE:
        cv2.ellipse(self.img, pos, color, thickness)
    except Exception, e:
      logging.exception("Output: Can't show result of %s", detector_name)

  def draw_hand(self, hand):
    """
    Draw hand contours and finger lines
    """
    try:
      if hand.contours != None and hand.hierarchy != None:
        draw.draw_contours(self.img, hand.contours, hand.hierarchy, self.colors["blue"], 0.7, hand.contours_offset)
        self.draw_fingers(hand)
      #if hand.contour != None:
      #  draw.draw_contour(self.img, hand.contour, self.colors["blue"], 0.7, hand.contours_offset)
      #  self.draw_fingers(hand)
    except Exception, e:
      logging.exception("Output: Can't draw contours")

  def draw_fingers(self, hand):
    """
    Draw each finger.
    """
    for finger in hand.fingers:
      draw.draw_lines(self.img, finger, self.colors["darkblue"])

  def toggle_estimate(self):
    """
    Show/hide estimate rectangle in final output
    """
    self.show_estimate = not self.show_estimate

  def toggle_detectors(self):
    """
    Show/hide detector rectangles in final output
    """
    self.show_detectors = not self.show_detectors

  def toggle_skin(self):
    """
    Show/hide skin contours in final output
    """
    self.show_skin = not self.show_skin

  def make_screenshot(self):
    timestamp = datetime.datetime.now() 
    filename = "{0}Screenshot {1}.jpg".format(self.screenshot_dir, timestamp)
    logging.info("Writing %s", filename)
    cv2.imwrite(filename, self.img)
