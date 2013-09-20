import os
from arith import is_number


def mac_command(app, cmd):
  """
  Make a system call using AppleScript
  """
  OSASCRIPT = '/usr/bin/osascript'
  scriptcmd = [OSASCRIPT,
      '-e', 'tell application "%s"' % app,
      '-e', '%s' % cmd,
      '-e', 'end tell']
  return os.spawnv(os.P_WAIT, scriptcmd[0], scriptcmd)

def mac_keyboard(modifiers, key):
  """
  A simple AppleScript keyboard wrapper
  """
  # Create key-down events for modifiers
  mod_keys = [mod + " down" for mod in modifiers]

  special_keys = {"F1": 101, "F2": 102, "F3": 103, "F4": 104, "F5": 105, "F6": 106,
      "F7": 107, "F8": 108, "F9": 109}
  key = special_keys.get(key, key)

  # Special keys use 'key code' call and
  # normal keys use 'keystroke' call in
  # AppleScript
  if is_number(key):
    send_key = "key code " + str(key)
  else:
    # If key is a single letter (e.g. "j" or "k"),
    # it must be escaped. Otherwise special keys like
    # "tab" or "space" would not work correctly.
    if len(key) == 1:
      key = '"' + key + '"'

    send_key = "keystroke " + key

  # Make the call
  cmd = '%s using {%s}' % (send_key, ", ".join(mod_keys))
  return mac_command("System Events", cmd)

def test():
  """
  Test keyboard functions
  """
  # Open new tab in iTerm2
  #mac_keyboard(["command"],"t")

  # Switch to previous application
  #mac_keyboard(["command"],"tab")

  # Multiple modifier keys
  #mac_keyboard(["shift", "command"],"p")

  # Single key test -> Switch tab in iTerm2
  #mac_keyboard(["command"],"j")

  # Mission Control / Expose
  #mac_keyboard([],"F1")

  # System settings
  #mac_keyboard(["Command"],"F1")
  #mac_command("System Preferences", "activate")

if __name__ == "__main__":
  test()
