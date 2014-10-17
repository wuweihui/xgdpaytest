#-*- coding: utf-8 -*-
#
# This program use google translate service to translate Chinese to English or like versa
# wei_cloud@126.com
#

import urllib, urllib2
import gzip, StringIO
import json, re
import wx
import threading
from wx.lib.embeddedimage import PyEmbeddedImage
import wx.media
from XGD.poslib.PosMsg import *

Devil = PyEmbeddedImage(
   "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"
   "kwAAAABJRU5ErkJggg==")
   
class MyTextDropTarget(wx.TextDropTarget):
   def __init__(self, window):
      wx.TextDropTarget.__init__(self)
      self.window = window
      
   def OnDropText(self, x, y, text):
      self.window.SetValue(text)
      
   def OnDragOver(self, x, y, d):
      return wx.DragCopy
      
class ReaderFrame(wx.Frame):
   def __init__(self, parent, title="Message Reader by wuweihui"):
      wx.Frame.__init__(self, parent, title=title, size=(850, 800), 
                        pos=(100, 100), style=wx.STAY_ON_TOP|wx.DEFAULT_FRAME_STYLE)
      self.SetBackgroundColour((255,255,255))
      self.SetIcon(Devil.GetIcon())
      
      font = wx.Font(10, wx.DEFAULT, wx.NORMAL, wx.NORMAL, False, 'Courier New')
      self.inputtc = wx.TextCtrl(self, -1, "", style=wx.TE_MULTILINE|wx.TE_PROCESS_TAB|wx.TE_PROCESS_ENTER)
      #self.inputtc.SetSize((300, 300))
      self.inputtc.SetFont(font)
      dt = MyTextDropTarget(self.inputtc)
      self.inputtc.SetDropTarget(dt)
      
      self.outputtc = wx.TextCtrl(self, -1, "", style=wx.TE_MULTILINE)
      self.outputtc.SetFont(font)
      
      sizer = wx.BoxSizer(wx.VERTICAL)
      sizer.Add(self.inputtc, 0, wx.EXPAND|wx.ALL, 5)
      sizer.Add(self.outputtc, 1, wx.EXPAND|wx.ALL, 5)
      
      self.btn = wx.Button(self, -1, "Parse")
      btnsizer = wx.BoxSizer(wx.HORIZONTAL)
      btnsizer.Add(self.btn, 0, wx.ALL, 5)
      sizer.Add(btnsizer, 0, wx.ALIGN_CENTER, 5)
      
      self.tbicon = TransTaskBarIcon(self)
      
      self.SetSizer(sizer)
      
      self.Bind(wx.EVT_BUTTON, self.OnParse, self.btn)
      self.Bind(wx.EVT_ICONIZE, self.OnHide)
      self.Bind(wx.EVT_CLOSE, self.OnClose)
      
   def OnParse(self, evt):
      """
[10/17 09:36:42.351][tcp2tux_v2-all][DBG][20755][    0] 00 D6 60 00 00 00 03 84 B7 E0 25 B1 02 38 34 39 34 34 30 33
[10/17 09:36:42.351][tcp2tux_v2-all][DBG][20755][   20] 35 33 31 31 36 30 33 31 38 30 30 31 34 30 39 39 00 00 00 00
[10/17 09:36:42.351][tcp2tux_v2-all][DBG][20755][   40] 00 00 00 00 00 A9 02 00 20 14 10 17 09 36 42 00 00 01 00 00
[10/17 09:36:42.351][tcp2tux_v2-all][DBG][20755][   60] 00 00 00 00 00 00 00 00 00 00 00 00 00 00 00 00 00 00 00 00
[10/17 09:36:42.351][tcp2tux_v2-all][DBG][20755][   80] 04 30 35 31 04 B9 96 24 02 25 03 00 72 43 00 41 10 69 24 5E
[10/17 09:36:42.351][tcp2tux_v2-all][DBG][20755][  100] 40 79 C3 A8 F6 5D 6B A0 6E C0 90 91 5C DC D0 7E 8F 42 10 0F
[10/17 09:36:42.351][tcp2tux_v2-all][DBG][20755][  120] 3A 46 7F 57 6C FF EB 99 F8 45 BA 16 AC 17 96 89 DD 8F 96 43
[10/17 09:36:42.351][tcp2tux_v2-all][DBG][20755][  140] 10 B9 BB 03 99 25 46 D8 87 92 85 88 AD 3B 69 C3 FC 3F 33 E2
[10/17 09:36:42.351][tcp2tux_v2-all][DBG][20755][  160] 15 00 2C 05 0A 00 0B 00 0C 00 29 1E 20 00 00 00 00 00 00 00
[10/17 09:36:42.351][tcp2tux_v2-all][DBG][20755][  180] 00 00 00 00 00 00 00 00 00 00 00 00 00 00 00 00 00 00 00 00
[10/17 09:36:42.351][tcp2tux_v2-all][DBG][20755][  200] 00 00 2D 03 00 00 01 00 00 00 00 00 00 00 00 0A
00:d6:60:00:00:00:03:84:81:c7:a8:25:02:38:34:39:34:34:30:33:35:33:31:31:36:30:33:31:38:30:30:31:34:30:39:39:00:00:00:00:00:00:00:00:00:a9:02:00:20:14:10:17:09:54:32:00:00:20:00:00:00:00:00:00:00:00:00:00:00:00:00:00:00:00:00:00:00:00:31:62:71:30:35:31:04:b9:96:24:02:25:03:00:72:43:00:41:10:fb:53:55:54:2a:38:28:32:bb:4f:b7:4d:f1:cf:2a:6e:4a:75:9d:3f:42:10:ad:a1:29:ef:d2:e8:c2:7b:a1:a3:fc:58:e3:02:74:78:fd:18:4a:97:43:10:2f:ad:e1:88:ce:8b:d2:b5:0f:68:5a:9a:03:d6:66:fa:37:dd:ad:eb:00:2c:05:0a:00:0b:00:0c:00:29:1e:20:00:00:00:00:00:00:00:00:00:00:00:00:00:00:00:00:00:00:00:00:00:00:00:00:00:00:00:00:00:2d:03:00:00:20:00:00:00:00:00:00:00:00:39
      """
      orig = self.inputtc.GetValue().strip()
      re_wireshark = re.compile('(\w\w\:+)+\w\w$')
      re_prefix = re.compile('\[.*\]', re.DOTALL)
      if re_wireshark.match(orig):
         orig = orig.replace(':', '')
      else:
         lines = orig.splitlines()
         newline = ''
         for line in lines:
            prefix = ' '
            if re_prefix.match(line):
               prefix = re_prefix.match(line).group()
            newline += line.replace(prefix, '')      
         orig = newline.replace(' ', '')
      
      #self.outputtc.SetValue(orig + '\n\n')
      out = self._print_fields(orig)
      self.outputtc.SetValue(orig + '\n\n' + out)
      
   def _print_fields(self, msg):
      out = ''
      if isinstance(msg, basestring):
         msg = Pos3Msg(msg)
      for k in msg.fields.keys():
         if msg.getShowFlag(k):            
            if isinstance(msg.getField(k), list):
               out += msg.getName(k) + ' : ' + str(map(str, msg.getField(k)))
               out += '\n'
            else:
               out += msg.getName(k) + ' : ' + str(msg.getField(k))
               out += '\n'
            if isinstance(msg.getField(k), OperationCodeBits):
               out += msg.getName(k) + ' : ' + str([i.codenumber for i in msg.getField(k).opcodes])
               out += '\n'
            if isinstance(msg.getField(k), Pos3MsgBase):
               out += self._print_fields(msg.getField(k))
               out += '\n'
      return out
      
   def OnClose(self, evt):
      self.tbicon.Destroy()
      self.Destroy()
      
   def OnHide(self, evt):
      self.Hide()
      
class TransTaskBarIcon(wx.TaskBarIcon):
   TBMENU_RESTORE = wx.NewId()
   TBMENU_CLOSE   = wx.NewId()
   
   def __init__(self, frame):
      wx.TaskBarIcon.__init__(self)
      self.frame = frame
      
      # Set the image
      icon = self.MakeIcon(Devil.GetImage())
      self.SetIcon(icon, "MessageReader")
      
      # bind some events
      self.Bind(wx.EVT_TASKBAR_LEFT_DCLICK, self.OnTaskBarActivate)
      self.Bind(wx.EVT_MENU, self.OnTaskBarActivate, id=self.TBMENU_RESTORE)
      self.Bind(wx.EVT_MENU, self.OnTaskBarClose, id=self.TBMENU_CLOSE)
      
      
   def CreatePopupMenu(self):
      """
        This method is called by the base class when it needs to popup
        the menu for the default EVT_RIGHT_DOWN event.  Just create
        the menu how you want it and return it from this function,
        the base class takes care of the rest.
        """
      menu = wx.Menu()
      menu.Append(self.TBMENU_RESTORE, "Restore Translator")
      menu.Append(self.TBMENU_CLOSE,   "Close Translator")
      return menu
      
      
   def MakeIcon(self, img):
      """
        The various platforms have different requirements for the
        icon size...
        """
      if "wxMSW" in wx.PlatformInfo:
         img = img.Scale(16, 16)
      elif "wxGTK" in wx.PlatformInfo:
         img = img.Scale(22, 22)
         # wxMac can be any size upto 128x128, so leave the source img alone....
      icon = wx.IconFromBitmap(img.ConvertToBitmap() )
      return icon
      
      
   def OnTaskBarActivate(self, evt):
      if self.frame.IsIconized():
         self.frame.Iconize(False)
      if not self.frame.IsShown():
         self.frame.Show(True)
      self.frame.Raise()
      
      
   def OnTaskBarClose(self, evt):
      wx.CallAfter(self.frame.Close)
      
      
class App(wx.App):

   def OnInit(self):
      self.frame = ReaderFrame(None)
      self.frame.Show(True)
      return True

if __name__ == "__main__":
   app = App(False)
   app.MainLoop()