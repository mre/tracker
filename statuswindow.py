"""
Based on the wx demo app "Miscellaneous : ShapedWindow".

Ray Pasco (WinCrazy)
pascor(at)verizon(dot)net

This code may be distributed and altered for any purpose whatsoever.
Use at you own risk. Printouts are suitable for framing or wrapping fish.
"""

import os, wx, time, signal, sys

class StatusWindow( wx.Frame ) :

    def __init__( self, imageFilename, opacity = 70 ) :

        self.max_opacity = opacity # Specified as a percentage.
        self.curr_opacity = 0 # Specified as a percentage.
        self.delta = 20 # Stepping for fadeIn and fadeOut
        self.transparencyMode = 0

        # Decoration-less and also borderless, "popup window" style
        style = ( wx.CLIP_CHILDREN | wx.STAY_ON_TOP | wx.FRAME_NO_TASKBAR |
                  wx.NO_BORDER | wx.FRAME_SHAPED )

        wx.Frame.__init__( self, None, style=style )

        # The image file must have a transparency layer to enable image bitmap transparency.
        # Window (overall) transparecy is set by the app.
        self.wxImage = wx.Image(imageFilename)

        self.bmap_unconvertedAplha = self.wxImage.ConvertToBitmap()
        self.wxImage.ConvertAlphaToMask( threshold=128 )
        self.bmap_convertedAlpha = self.wxImage.ConvertToBitmap()

        self.bmap = self.bmap_convertedAlpha

        popupSizeX, popupSizeY = self.bmap.GetSize()    # Alt: (self.bmap.GetWidth(), self.bmap.GetHeight())
        self.viewableSize = (popupSizeX, popupSizeY)
        self.SetClientSize( self.viewableSize )

        # Exactly center the completed popup window in the screen.
        screenSizeX, screenSizeY = wx.DisplaySize()
        popupPosn = ((screenSizeX-popupSizeX)/2, (screenSizeY-popupSizeY)/2)
        self.SetPosition( popupPosn )

        self.Bind( wx.EVT_LEFT_DOWN, self.closeWindow)  # An easy way to quit..
        self.Bind( wx.EVT_PAINT, self.OnPaint )         # Just calls self.DrawShapedWindow()
        #self.Bind( wx.EVT_KEY_DOWN, self.OnKeyDown )    # <ESC>, Q or q to quit the app
        #self.Bind( wx.EVT_MOTION, self.OnMotion )       # Implement optional window dragging
        #self.Bind( wx.EVT_LEFT_DCLICK, self.OnDoubleClick )

        if wx.Platform == "__WXGTK__":
            # wxGTK requires that the window be created before you can set its shape,
            # so delay the call to SetWindowTransparencies until this event.
            # This event just calls SetWindowTransparencies()
            self.Bind( wx.EVT_WINDOW_CREATE, self.OnDoubleClick )

        self.Show( True )       # Just for GTK's wx.EVT_WINDOW_CREATE
        self.Show( False )      # Avoid an annoying white window flash
        self.SetWindowTransparencies(self.curr_opacity)
        self.Show()
        self.FadeIn()


    def FadeInStep(self, evt):
        self.curr_opacity += self.delta
        if self.curr_opacity >= self.max_opacity:
            self.curr_opacity = self.max_opacity
            self.timer.Stop()
        self.SetTransparencyPercentage(self.curr_opacity)

    def FadeOutStep(self, evt):
        self.curr_opacity -= self.delta
        if self.curr_opacity <= 0:
            self.curr_opacity = 0
            self.Close( force=True )
            #self.timer.Stop()
        self.SetTransparencyPercentage(self.curr_opacity)

    def FadeIn(self):
        ## ------- Fader Timer -------- ##
        self.timer = wx.Timer(self, wx.ID_ANY)
        self.timer.Start(60)
        self.Bind(wx.EVT_TIMER, self.FadeInStep)
        ## ---------------------------- ##

    def FadeOut(self):
        ## ------- Fader Timer -------- ##
        self.timer = wx.Timer(self, wx.ID_ANY)
        self.timer.Start(60)
        self.Bind(wx.EVT_TIMER, self.FadeOutStep)
        ## ---------------------------- ##

    def SetTransparencyPercentage(self, opacity_percentage):
        self.SetTransparent( opacity_percentage * 255 / 100 )

    def SetWindowTransparencies( self, opacity = 100) :

        if   self.transparencyMode == 0 :
            # Partial window (overall) transparency
            self.SetTransparent( opacity * 255 / 100 )
            # Bitmap transparency enabled (cn't see background)
            self.bmap = self.bmap_convertedAlpha
            self.SetShape( wx.RegionFromBitmap( self.bmap ) )

        elif self.transparencyMode == 1 :
            # No window transparency (what bitmaps mask shows is 100% opaque)
            self.SetTransparent( 255 )
            # Bitmap transparency enabled
            self.bmap = self.bmap_convertedAlpha
            self.SetShape( wx.RegionFromBitmap( self.bmap ) )

        elif self.transparencyMode == 2 :
            # No window transparency (what is seen is 100% opaque)
            self.SetTransparent( 255 )
            # Bitmap transparency mask is disabled
            self.bmap = self.bmap_unconvertedAplha
            self.SetShape( wx.Region() )

        self.transparencyMode += 1
        if self.transparencyMode > 2 :    self.transparencyMode = 0

    def OnPaint( self, event ) :
        self.DrawShapedWindow()
        event.Skip() # Required for using a wx.ClientDC

    def DrawShapedWindow( self ) :
        if wx.Platform == '__WXGTK__' :
            dc = wx.GCDC( wx.ClientDC( self ) )
        else :
            dc = wx.ClientDC( self )        # This is OK for MSW
        dc.DrawBitmap( self.bmap, 0, 0, True )

    def closeWindow( self, event ) :
      self.FadeOut()

    def OnKeyDown( self, event ) :
        """Press Q, q or <ESC>"""

        quitCodes = [ 27, ord('Q'), ord('q')  ]     # Reasonable, but arbitrary keys.
        if event.GetKeyCode() in quitCodes :
            self.Close( force=True )

        event.Skip()

    def OnMotion( self, event ) :
        """
        Implement window dragging since this window has no frame to grab.
        In reality, I've never seen a popup window that the user could move,
        but this method demostrates a concise and not-very-obvious technique.
        """

        if not event.Dragging() :       # Mouse is moving but no button is down.
            self.CaptureMouse()
            self.dragPosn = event.GetPosition()
            return

        # LeftMouse is now down.
        self.CaptureMouse()                 # Store the current postion for event.GetPosition()
        currentPosn = event.GetPosition()   # get it now and not embedded within the next statement
        displacement = self.dragPosn - currentPosn     # always nonzero
        newPosn = self.GetPosition() - displacement
        self.SetPosition( newPosn )

        event.Skip()


def InstallTermHandler(callback, *args, **kwargs):
    """Install exit app handler for sigterm (unix/linux)
    and uses SetConsoleCtrlHandler on Windows.
    @param callback: callable(*args, **kwargs)
    @return: bool (installed or not)

    """
    assert callable(callback), "callback must be callable!"

    installed = True
    if wx.Platform == '__WXMSW__':
        if HASWIN32:
            win32api.SetConsoleCtrlHandler(lambda dummy :
callback(*args, **kwargs),
                                           True)
        else:
            installed = False
    else:
        signal.signal(signal.SIGTERM,
                           lambda signum, frame : callback(*args, **kwargs))
        signal.signal(signal.SIGINT,
                           lambda signum, frame : callback(*args, **kwargs))

    return installed

def SignalHandler(*args, **kwargs):
  print "lol"

def show_sign(sign, opacity = 70):
  signs = ["ok", "calibrating", "waiting"]
  if sign not in signs:
    return

  img = 'assets/' + sign + '.png'
  try:
    with open(img):
      myApp = wx.App(redirect=False) # Any error messages go to the command window.
      appFrame = StatusWindow(img, opacity) # GTK requires the window to be complete before .Show()
      myApp.MainLoop()
  except IOError:
    print "Can't open file", img
    sys.exit()

if __name__ == "__main__":
  show_sign("calibrating")

