#!/usr/bin/env python
#-*- coding: utf-8 -*-

"""
Robust realtime gesture recognition.
====================================

The goal of this work is to achive robust real-time capable detection 
of a user’s hand movement from webcam-captured live video by
building a pipeline of detector algorithms.

(C) 2013 Matthias Endler
Code adapted from Yeison Cardona (yeison.eng@gmail.com) (C) 2012

This library is free software; you can redistribute it and/or
modify it under the terms of the GNU Lesser General Public
License as published by the Free Software Foundation; either
version 2.1 of the License, or (at your option) any later version.

This library is distributed in the hope that it will be useful,
but WITHOUT ANY WARRANTY; without even the implied warranty of
MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE. See the GNU
Lesser General Public License for more details.

You should have received a copy of the GNU Lesser General Public
License along with this library; if not, write to the Free Software
Foundation, Inc., 51 Franklin Street, Fifth Floor, Boston, MA 02110-1301 USA
"""

# External libraries
import cv, cv2
import time, threading, operator, math, datetime, errno
from os import listdir
import colorsys
from collections import namedtuple
import numpy as np
from numpy import sqrt, arccos, rad2deg
import logging

# Own modules
from filters import Filters
from detector import Detector
from gesture import Gesture
from hand import Hand
import rectangle
from keyboard import mac_keyboard
import geom
import draw
from kb import KB
from action import Action, Actions
from output import Output

class Tracker(object):
  """
  This is the main program which gives a high-level view
  of all the running subsystems. It connects camera input with
  output in form of "actions" (such as keyboard shortcuts on the users behalf).
  This is done by locating a hand in an image and detecting features,
  like the number of fingers, and trying to match that data with a
  known gesture.
  """

  def __init__(self):
    """
    Configuration
    """

    # Camera settings
    self.FRAME_WIDTH = 341
    self.FRAME_HEIGHT = 256
    self.flip_camera = True # Mirror image
    self.camera = cv2.VideoCapture(1)

    # ...you can also use a test video for input
    #video = "/Users/matthiasendler/Code/snippets/python/tracker/final/assets/test_video/10.mov"
    #self.camera = cv2.VideoCapture(video)
    #self.skip_input(400) # Skip to an interesting part of the video

    if not self.camera.isOpened():
        print "couldn't load webcam"
        return
    #self.camera.set(cv2.cv.CV_CAP_PROP_FRAME_WIDTH, self.FRAME_WIDTH)
    #self.camera.set(cv2.cv.CV_CAP_PROP_FRAME_HEIGHT, self.FRAME_HEIGHT)

    self.filters_dir = "filters/" # Filter settings in trackbar
    self.filters_file = "filters_default"

    # Load filter settings
    current_config = self.filters_dir + self.filters_file
    self.filters = Filters(current_config)

    # No actions will be triggered in test mode
    # (can be used to adjust settings at runtime)
    self.test_mode = False

    # Create a hand detector
    # In fact, this is a wrapper for many detectors
    # to increase detection confidence
    self.detector = Detector(self.filters.config)

    # Knowledge base for all detectors
    self.kb = KB()
    # Create gesture recognizer.
    # A gesture consists of a motion and a hand state.
    self.gesture = Gesture()

    # The action module executes keyboard and mouse commands
    self.action = Action()

    # Show output of detectors
    self.output = Output()

    self.run()

  def run(self):
    """
    In each step: Read the input image and keys,
    process it and react on it (e.g. with an action).
    """
    while True:
      img = self.get_input()
      hand = self.process(img)
      ref = self.action.get_reference_point()
      self.output.show(img, hand, ref)

  def process(self, img):
    """
    Process input
    """
    # Run detection
    hand = self.detector.detect(img)
    # Store result in knowledge base
    self.kb.update(hand)
    if not self.test_mode:
      # Try to interprete as gesture
      self.interprete(hand)
    return hand

  def interprete(self, hand):
    """
    Try to interprete the input as a gesture
    """
    self.gesture.add_hand(hand)
    operation = self.gesture.detect_gesture()
    self.action.execute(operation)

  def get_input(self):
    """
    Get input from camera and keyboard
    """
    self.get_key()
    _, img = self.camera.read()
    img = cv2.resize(img, (self.FRAME_WIDTH, self.FRAME_HEIGHT))
    if self.flip_camera:
      img = cv2.flip(img, 1)
    return img


  def get_key(self):
    """
    Read keyboard input
    """
    key = cv2.waitKey(self.filters.config["wait_between_frames"])
    if key == ord('+'):
      # Reduce program speed
      self.filters.config["wait_between_frames"] += 500
    if key == ord('-'):
      # Increase program speed
      if self.filters.config["wait_between_frames"] >= 500:
        self.filters.config["wait_between_frames"] -= 500
    #if key == ord('s'):
    # Save config
    #  self.filters.save()
    if key == ord('r'):
      # Reset all detectors
      self.detector.reset()
      self.action.reset()
    if key == ord('d'):
      # Make a screenshot
      self.output.make_screenshot()
    if key == ord('p') or key == ord(' '):
      # Pause
      cv2.waitKey()
    if key == ord('t'):
      # Test mode
      self.test_mode = not self.test_mode
    if key == ord('1'):
      self.output.toggle_estimate()
    if key == ord('2'):
      self.output.toggle_detectors()
    if key == ord('3'):
      self.output.toggle_skin()
    if key == ord('f'):
      self.toggle_filters()
    if key == 63235: # Right arrow
      self.skip_input(20)
    if key == 27 or key == ord('q'):
      # Abort program on ESC, q or space
      exit()

  def toggle_filters(self):
    """
    Load the next filter settings
    """
    self.filters_file = self.next_filters_file()
    current_config = self.filters_dir + self.filters_file
    self.filters.set_config(current_config)

  def next_filters_file(self):
    """
    Get the next filter settings
    """
    filters = listdir(self.filters_dir)
    for i, f in enumerate(filters):
      if f == self.filters_file:
        return filters[(i+1) % len(filters)]

  def skip_input(self, x=1):
    """
    Skip to a different part of a video sequence.
    """
    for i in range(0,x):
      self.camera.grab()

if __name__=='__main__':
  """
  Start program with a logger
  """
  logging.basicConfig(#filename = 'confidence.log',
                      format   = '%(message)s',
                      level    = logging.INFO)
  Tracker()
