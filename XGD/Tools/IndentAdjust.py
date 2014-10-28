#-*- coding: utf-8 -*-

import wx
from wx.lib import masked
import os

Tab_Space = 3
Indent_Space = 3

def IndentAdjust(src, dst):
   with open(src, 'rb') as fp:
      code = fp.read()
      
   code.expandtabs(Tab_Space)
   #Get the indent level for each line
   lines = code.splitlines()
   levels = []
   level = 0
   pre_indent = [0,]
   comment = False
   extandline = False
   for n in range(len(lines)):
      line = lines[n]
      if line.strip() and not line.strip().startswith('#'):         
         if comment:
            levels.append(-1)
            if line.find("\"\"\"") != -1 and line.count("\"\"\"")%2 != 0:
               comment = not comment
            continue         
         
         stripline = (line + ' ')[:line.find('#')].strip()
         if extandline:
            levels.append(-1)
            extandline = False
            if stripline.endswith('\\') or stripline.endswith(','):
               extandline = True
            continue
         
         if stripline.startswith('|') or stripline.startswith(')')\
            or stripline.startswith(']') or stripline.startswith('}'):
            levels.append(-1)
            continue
         
         for i in range(len(line)):
            if not line[i].isspace():
               break
         indent = i
         if indent < pre_indent[-1]:
            try:
               level = pre_indent.index(indent)
            except:
               raise RuntimeError("Code style error! Indent did not match at line %d\nPlease check your code first!" % n)
            pre_indent = pre_indent[:level+1]
         if indent == pre_indent[-1]:
            level = len(pre_indent) - 1
         if indent > pre_indent[-1]:
            level = len(pre_indent)
            pre_indent.append(indent)
            #print i, level, line
         
         if stripline.endswith('\\') or stripline.endswith(','):
            extandline = True
         
         if line.find("\"\"\"") != -1 and line.count("\"\"\"")%2 != 0:
            comment = not comment   
         
      levels.append(level)
   
   if comment:
      RuntimeError("Code style error! Comment did not match!")
   
   for i in range(len(lines)):
      if levels[i] == -1:
         continue
      lines[i] = ' '*levels[i]*Indent_Space + lines[i].strip()
      
      #print '\n'.join(lines)
   with open(dst, 'wb') as fp:
      fp.write('\n'.join(lines))
      
class MyFileDropTarget(wx.FileDropTarget):
   def __init__(self, win):
      wx.FileDropTarget.__init__(self)
      self.win = win
      
   def OnDropFiles(self, x, y, filenames):
      fpath = filenames[0]
      self.win.spathtc.SetValue(fpath)
      self.win.dpathtc.SetValue(fpath)
      
      
class IndentAdjustFrame(wx.Frame):
   def __init__(self, parent, id=-1):
      wx.Frame.__init__(self, parent, id, 'Code Indent Convert Frame by wuweihui')
      
      self.panel = wx.Panel(self, -1)
      space = 5
      mainsizer = wx.BoxSizer(wx.VERTICAL)
      
      sizer = wx.BoxSizer(wx.HORIZONTAL)
      st = wx.StaticText(self.panel, -1, 'src')
      self.spathtc = wx.TextCtrl(self.panel, -1, '')
      srcbtn = wx.Button(self.panel, -1, 'Open')
      sizer.Add(st, 0, wx.EXPAND|wx.ALL, space)
      sizer.Add(self.spathtc, 1, wx.EXPAND|wx.ALL, space)
      sizer.Add(srcbtn, 0, wx.EXPAND|wx.ALL, space)
      mainsizer.Add(sizer, 0, wx.EXPAND|wx.ALL, 0)
      
      sizer = wx.BoxSizer(wx.HORIZONTAL)
      st = wx.StaticText(self.panel, -1, 'dst')
      self.dpathtc = wx.TextCtrl(self.panel, -1, '')
      dstbtn = wx.Button(self.panel, -1, 'Open')
      dstbtn.Disable()
      sizer.Add(st, 0, wx.EXPAND|wx.ALL, space)
      sizer.Add(self.dpathtc, 1, wx.EXPAND|wx.ALL, space)
      sizer.Add(dstbtn, 0, wx.EXPAND|wx.ALL, space)
      mainsizer.Add(sizer, 0, wx.EXPAND|wx.ALL, 0)
      
      sizer = wx.BoxSizer(wx.HORIZONTAL)
      st = wx.StaticText(self.panel, -1, 'Source Tab Space')
      #self.ts = wx.TextCtrl(self.panel, -1, str(Tab_Space))
      self.ts = masked.NumCtrl(self.panel, value=Tab_Space, allowNegative=False)
      sizer.Add(st, 0, wx.EXPAND|wx.ALL, space)
      sizer.Add(self.ts, 0, wx.EXPAND|wx.ALL, space)
      
      st = wx.StaticText(self.panel, -1, 'Target Indent Space')
      #self.tis = wx.TextCtrl(self.panel, -1, str(Indent_Space))
      self.tis = masked.NumCtrl(self.panel, value=Indent_Space, allowNegative=False)
      sizer.Add(st, 0, wx.EXPAND|wx.ALL, space)
      sizer.Add(self.tis, 0, wx.EXPAND|wx.ALL, space)
      mainsizer.Add(sizer, 0, wx.EXPAND|wx.ALL, 0)
      
      sizer = wx.BoxSizer(wx.HORIZONTAL)
      okbtn = wx.Button(self.panel, wx.ID_OK, 'Convert')
      cancelbtn = wx.Button(self.panel, wx.ID_CANCEL, 'Close')
      sizer.Add(okbtn, 0, wx.EXPAND|wx.ALL, space)
      sizer.Add(cancelbtn, 0, wx.EXPAND|wx.ALL, space)
      mainsizer.Add(sizer, 0, wx.ALIGN_CENTER, space)
      
      #set Drop target
      dt = MyFileDropTarget(self)
      self.spathtc.SetDropTarget(dt)
      
      self.panel.SetSizer(mainsizer)
      self.panel.Fit()
      self.Fit()
      
      #Bind events
      self.Bind(wx.EVT_BUTTON, self.OnConvert, okbtn)
      self.Bind(wx.EVT_BUTTON, self.OnClose, cancelbtn)
      self.Bind(wx.EVT_BUTTON, self.OnOpenSrc, srcbtn)
      
   def OnConvert(self, evt):
   #Set env
      global Tab_Space, Indent_Space
      Tab_Space = int(self.ts.GetValue())
      Indent_Space = int(self.tis.GetValue())
      
      try:
         IndentAdjust(self.spathtc.GetValue(), self.dpathtc.GetValue())
         dlg = wx.MessageDialog(self, "Conversion complete!",
            'Confirm',
            wx.OK | wx.ICON_INFORMATION
            #wx.YES_NO | wx.NO_DEFAULT | wx.CANCEL | wx.ICON_INFORMATION
            )
         dlg.ShowModal()
         dlg.Destroy()
      except Exception, e:
         dlg = wx.MessageDialog(self, "Conversion Failed!\n%s" % e.message,
            'Alert',
            wx.OK | wx.ICON_INFORMATION
            #wx.YES_NO | wx.NO_DEFAULT | wx.CANCEL | wx.ICON_INFORMATION
            )
         dlg.ShowModal()
         dlg.Destroy()
         
   def OnClose(self, evt):
      self.Destroy()
      
   def OnOpenSrc(self, evt):
      dlg = wx.FileDialog(self, message="Choose a file",
         defaultDir=os.getcwd(),
         defaultFile="",
         wildcard="Python source (*.py)|*.py|All files (*.*)|*.*",
         style=wx.OPEN | wx.CHANGE_DIR
         )
      if dlg.ShowModal() == wx.ID_OK:
         path = dlg.GetPath()
         self.spathtc.SetValue(path)
         self.dpathtc.SetValue(path)
         
      dlg.Destroy()
      
class App(wx.App):

   def OnInit(self):
      self.frame = IndentAdjustFrame(None)
      self.frame.Show(True)
      return True
      
if __name__ == "__main__":
   app = App(False)
   app.MainLoop()
   