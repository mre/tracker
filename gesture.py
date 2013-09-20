import math
from action import Actions
import time

class Gesture:
  """
  Try to interpret the detected hand positions and the number
  of fingers as a gesture
  """
  def __init__(self, duration=2):

    # Minimal duration for each gesture in number of frames
    self.duration = duration

    # Keep two more frames in history for outliers
    self.history_length = duration + 2

    # A gesture is defined by a symbol and the number of
    # fingers which trigger the gesture.
    self.gestures = {
      # Name: {fingers, action, delay between same gesture}
      #"Overview":  {"fingers": [5], "action": Actions.EXPOSE, "delay": 5.0},
      "Point": {"fingers": [2], "action": Actions.POINTER,  "delay": 0},
      #"Move":  {"fingers": [2], "action": Actions.MOVEWIN,  "delay": 0}
    }

    # Remember the last action and the execution time
    self.last_action = (None, None)

    # Hand history
    self.hands = []

  def reset_history(self):
    self.hands = []

  def add_hand(self, hand):
    """
    New hand properties (position, shape) have been detected.
    Update hand history
    """
    self.hands.append(hand)
    # Only keep the last few hands
    self.hands = self.hands[-self.history_length:]

  def all_same(self, items):
    """
    Check if all elements in the list are the same.
    From http://stackoverflow.com/a/3787983/270334
    """
    return all(x == items[0] for x in items)

  def detect_gesture(self):
    """
    Detect gestures, which occured during the last few frames
    """
    # Have enough frames for futher analysis
    # We need two extra frames to remove max/min outliers.
    if len(self.hands) < self.history_length:
      # Not enough hands yet
      return None

    # Detect number of fingers during last few frames
    fingers = [h.num_fingers for h in self.hands]

    # Remove max/min outliers
    fingers = sorted(fingers)
    fingers = fingers[1:-1]

    #print fingers
    if not self.all_same(fingers):
      return None

    num_fingers = fingers[0]

    # Check for gesture
    for gesture, params in self.gestures.items():
      gesture_fingers = params["fingers"]
      if num_fingers in gesture_fingers:
        return self.trigger(params["action"], params["delay"])
    return None

  def trigger(self, action, delay):
    """
    Triggers an action if the delay has passed
    """
    if self.valid_action(action, delay):
        # Store action
        self.last_action = (action, time.time())
        return action

  def valid_action(self, a, delay):
    """
    Ignore the action, if it has been triggered too frequently.
    """
    # Different action than the last one?
    prev_action, prev_time = self.last_action
    if prev_action != a:
      return True

    # Same action. Has enough time passed since last call?
    delta = time.time() - prev_time
    return delta > delay
