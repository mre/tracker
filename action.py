import keyboard
from kb import KB
from hand import Hand
import logging
import rectangle
#from pymouse import PyMouse
from keyboard import mac_command, mac_keyboard
import time
from pykeyboard import PyKeyboard


class Actions(object):
  """
  List all possible actions here
  """
  EXPOSE  = 1 # Show all windows
  POINTER = 2 # Use hand to control the mouse pointer
  MOVEWIN = 3 # Use hand to move the window under the cursor

class Action(object):
  """
  Desktop environment control.
  Executes shortcuts and mouse actions on behalf of the user.
  Currently, only Mac OS X shortcuts are supported.

  The Action class keeps an internal state (e.g. current pressed keys,
  the first hand position of a gesture) to allow more complex movements like
  window movement.
  """
  def __init__(self):
    # Access knowledge base to check hand state
    self.kb = KB()
    # Platform independent mouse support
    #self.m = PyMouse()
    # Remember which keys are pressed
    # in order to release them after the gesture
    self.pressed_keys = []
    # Remember the first hand position for smoother mouse movement
    self.reference_point = None
    # Only move mouse if we recognize significant hand movement
    self.movement_threshold = 30
    # If no action has been triggered for a long time,
    # the internal state becomes invalid.
    self.reset_duration = 5
    self.last_command_time = time.time()

    self.KeyUp = 126
    self.KeyDown = 125
    self.KeyLeft = 123
    self.KeyRight = 124

    self.k = PyKeyboard()

  def execute(self, action):
    """
    React on a gesture (trigger an action) on valid input
    """
    if action:
      self.action_triggered()
      self.call_handler(action)

    if self.no_current_actions():
      self.reset()

  def no_current_actions(self):
    """
    Check if too much time has passed since the last action and
    therefore the internal state became invalid.
    """
    time_since_last_cmd = time.time() - self.last_command_time
    return time_since_last_cmd > self.reset_duration

  def action_triggered(self):
    """
    Store time of action for later reference.
    """
    self.last_command_time = time.time()

  def call_handler(self, action):
    """
    Execute a handler for an action
    """
    if action == Actions.EXPOSE:
      self.expose_handler()
    elif action == Actions.POINTER:
      #self.pointer_handler()
      self.keyboard_handler()
    elif action == Actions.MOVEWIN:
      self.window_handler()

  def expose_handler(self):
    """
    Run expose / Mission control
    """
    keyboard.mac_keyboard([],"F1") 

  def keyboard_handler(self):
    """
    Provides an action interface to the keyboard
    """
    dx, dy = self.get_movement(False)
    if abs(dx) > abs(dy):
      if dx < 0:
        print "right"
        self.k.press_key(self.KeyRight)
        #mac_keyboard([], "d")
      else:
        print "left"
        self.k.press_key(self.KeyLeft)
        #mac_keyboard([], "a")
    else:
      if dy < 0:
        print "down"
        self.k.press_key(self.KeyDown)
        #mac_keyboard([], "s")
      else:
        print "up"
        self.k.press_key(self.KeyUp)
        #mac_keyboard([], "w")

  def pointer_handler(self):
    """
    Handle mouse movement
    """
    dx, dy = self.get_movement()
    #self.move_mouse(dx,dy)

  def window_handler(self):
    """
    Handle window movement command.
    """
    dx, dy = self.get_movement()
    #self.move_win(dx,dy)

  def get_movement(self, relative=True):
    """
    Determine the window movement during the last two frames.
    This might go wrong if the history is not long enough but
    it's easier to ask for forgiveness than permission... ;-)
    """
    try:
      h = self.kb.history
      curr = h[-1].pos["estimate"]

      # Store the first hand position of the gesture for later
      if not self.reference_point:
        prev_estimate = h[-2].pos["estimate"]
        reference_rect = prev_estimate.pos
        self.reference_point = rectangle.center(reference_rect)

      # Get center of hand
      curr_center = rectangle.center(curr.pos)

      # Movement
      if relative:
        dx, dy = self.diff_rel(self.reference_point, curr_center)
      else:
        dx, dy = self.diff_abs(self.reference_point, curr_center)
      return (dx, dy)
    except Exception, e:
      logging.exception("Action: Error while calculating motion")
      return (0,0)

  def diff_rel(self, p_new, p_old):
    """
    Relative difference of two points
    """
    deltax, deltay = self.diff_abs(p_new, p_old)
    dx = dy = 0
    if deltax > self.movement_threshold:
      dx = -20
    elif deltax < self.movement_threshold:
      dx = 20
    if deltay > self.movement_threshold:
      dy = -20
    elif deltay < self.movement_threshold:
      dy = 20
    return (dx, dy)

  def diff_abs(self, p_new, p_old):
    """
    Absolute difference of two points
    """
    x_new, y_new = p_new
    x_old, y_old = p_old
    dx = x_new - x_old
    dy = y_new - y_old
    return (dx, dy)

  def move_mouse(self, dx, dy):
    """
    Mouse movement
    """
    if dx == 0 and dy == 0:
      return
    try:
      x_old, y_old = self.m.position()
      x_new = max(0, x_old + dx)
      y_new = max(0, y_old + dy)
      self.m.move(x_new, y_new)
    except Exception, e:
      logging.exception("Action: Error while moving mouse")

  def move_win(self, dx, dy):
    """
    Window movement
    """
    if dx == 0 and dy == 0:
      return
    try:
      x_old, y_old = self.m.position()
      x_new = max(0, x_old + dx)
      y_new = max(0, y_old + dy)
      self.press("command")
      self.m.press(x_old, y_old)
      self.m.move(x_new, y_new)
      self.m.release(x_new, y_new)
    except Exception, e:
      logging.exception("Action: Error while moving window")
      # Restore system defaults
      self.reset()

  def press(self, key):
    """
    Press a key and remember state.
    """
    if key in self.pressed_keys:
      # Already pressed
      return
    cmd = "key down {}".format(key)
    mac_command("System Events", cmd)
    self.pressed_keys.append(key)

  def release(self, key):
    """
    Release a key and remember state.
    """
    if key not in self.pressed_keys:
      # Not pressed
      return
    cmd = "key up {}".format(key)
    mac_command("System Events", cmd)
    self.pressed_keys.remove(key)

  def reset(self):
    """
    Release keys after a command.
    """
    logging.debug("Action: Resetting state. Pressed keys %s", self.pressed_keys)
    for k in self.pressed_keys:
      self.release(k)
    self.reference_point = None

  def get_reference_point(self):
    return self.reference_point
