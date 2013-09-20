import pickle, cv2
import logging
import datetime

class Filters(object):
  """
  Filters are used to adjust the settings during runtime.
  """

  def __init__(self, config):
    # Config dictionary
    self.config = dict()

    # Config file
    self.current_config = config
    self.winname = ""

    # Load settings file, but don't update trackbar yet
    self.load(False)

    # Number of "ticks" in trackbar for floating point values
    # The more ticks, the more accurate the value can be adjusted.
    self.float_scale = 10

    self.show_filters()

  def show_filters(self):
    """
    Create a trackbar for every setting.
    """
    cv2.namedWindow(self.winname)
    cv2.createTrackbar("Max hue"        , self.winname , self.config["max_hue"]        , 180 , self.on_change_max_hue)
    cv2.createTrackbar("Min hue"        , self.winname , self.config["min_hue"]        , 180 , self.on_change_min_hue)
    cv2.createTrackbar("Max saturation" , self.winname , self.config["max_saturation"] , 255 , self.on_change_max_saturation)
    cv2.createTrackbar("Min saturation" , self.winname , self.config["min_saturation"] , 255 , self.on_change_min_saturation)
    cv2.createTrackbar("Max darkness"   , self.winname , self.config["max_darkness"]   , 255 , self.on_change_max_darkness)
    cv2.createTrackbar("Min darkness"   , self.winname , self.config["min_darkness"]   , 255 , self.on_change_min_darkness)
    cv2.createTrackbar("Erode"          , self.winname , self.config["erode"]          , 20  , self.on_change_erode)
    cv2.createTrackbar("Dilate"         , self.winname , self.config["dilate"]         , 20  , self.on_change_dilate)
    cv2.createTrackbar("Smooth"         , self.winname , self.config["smooth"]         , 20  , self.on_change_smooth)


  def set_val(self, param, value):
    """
    Set a config variable to a new value 
    """
    self.config[param] = value
    logging.info("Filter: Setting %s to %s", param, value)

  def set_trackbar(self, param, value):
    """
    Set trackbar position
    """
    trackbar_name = self.var_to_description(param)
    cv2.setTrackbarPos(trackbar_name, self.winname, value)

  def on_change_max_hue(self, value):
    print "call"
    self.set_val("max_hue", value)
    if value < self.config["min_hue"]:
      self.set_trackbar("min_hue", value)

  def on_change_min_hue(self, value):
    self.set_val("min_hue", value)
    if value > self.config["max_hue"]:
      self.set_trackbar("max_hue", value)

  def on_change_max_saturation(self, value):
    self.set_val("max_saturation", value)
    if value < self.config["min_saturation"]:
      self.set_trackbar("min_saturation", value)

  def on_change_min_saturation(self, value):
    self.set_val("min_saturation", value)
    if value > self.config["max_hue"]:
      self.set_trackbar("max_saturation", value)

  def on_change_max_darkness(self, value):
    self.set_val("max_darkness", value)
    if value < self.config["min_darkness"]:
      self.set_trackbar("min_darkness", value)

  def on_change_min_darkness(self, value):
    self.set_val("min_darkness", value)
    if value > self.config["max_darkness"]:
      self.set_trackbar("max_darkness", value)

  def on_change_erode(self, value):
    self.set_val("erode", value)

  def on_change_dilate(self, value):
    self.set_val("dilate", value)

  def on_change_smooth(self, value):
    self.set_val("smooth", value)

  def save(self):
    """
    Store current configuration on disk
    """
    timestamp = datetime.datetime.now()
    filename = "{0}-{1}".format(self.current_config, timestamp)
    pickle.dump(self.config, open(filename, "w"))
    print "Saved new config file:", filename

  def set_config(self, config):
    """
    Set new config options
    """
    self.current_config = config
    self.load()

  def var_to_description(self, var):
    """
    Get the name of a trackbar option from its variable name
    """
    var = str.capitalize(var)
    return var.replace("_" , " ")

  def get_value(self, val):
    """
    The trackbar only accepts integer values. Float values
    need to be converted
    """
    print "converting", val
    if isinstance(val, int):
      return val
    # Magic float "conversion"
    return int(val * self.float_scale)

  def update_trackbar(self):
    """
    After loading a new configuration, update all trackbar positions
    """
    try:
      for key, val in self.config.iteritems():
        desc = self.var_to_description(key)
        val = self.get_value(val)
        cv2.setTrackbarPos(desc, self.winname, val)
    except:
      logging.exception("Filter: Error loading new configuration file.")

  def load(self, update=True):
    """
    Load configuration from disk.
    """
    try:
      logging.info("Loading %s..." % (self.current_config))
      self.config.update(pickle.load(open(self.current_config, "r")))
      logging.info(self.config)
      if update:
        self.update_trackbar()

    except Exception, e:
      logging.exception("Config file %s not found.", self.current_config)
