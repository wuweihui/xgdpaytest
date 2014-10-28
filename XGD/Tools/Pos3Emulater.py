#-*- coding: utf-8 -*-
import wx
import wx.aui
import wx.lib.scrolledpanel as scrolled 
import os
import re
import threading
from wx.lib.embeddedimage import PyEmbeddedImage
from XGD.poslib.PosMsg import *
from XGD.poslib.PosLibrary import PosLibrary
from SSHClient import *


def Courier_New(size=10):
   return wx.Font(size, wx.DEFAULT, wx.NORMAL, wx.NORMAL, False, 'Courier New')

class MessageBuilder(wx.Panel):
   def __init__(self, parent, id=-1, frame=None):
      wx.Panel.__init__(self, parent, id, style=wx.TAB_TRAVERSAL|wx.CLIP_CHILDREN)
      self.SetFont(Courier_New())
      self.frame = frame
      self.autoid = True
            
      self.fieldpanel = scrolled.ScrolledPanel(self, -1, style=wx.TAB_TRAVERSAL|wx.SUNKEN_BORDER)
      self.vsizer = wx.BoxSizer(wx.VERTICAL)
      self.fieldpanel.SetSizer(self.vsizer)
      self.fieldpanel.SetupScrolling()
            
      self.messagetc = wx.TextCtrl(self, -1, '', style=wx.TE_MULTILINE|wx.TE_PROCESS_ENTER)
      self.sendbtn = wx.Button(self, -1, 'SendMessage')
      
      mainsizer = wx.BoxSizer(wx.VERTICAL)
      space = 5
      hsizer = wx.BoxSizer(wx.HORIZONTAL)
      hsizer.Add(self.messagetc, 1, wx.EXPAND|wx.ALL, space)
      hsizer.Add(self.sendbtn, 0, wx.EXPAND|wx.ALL, space)
            
      mainsizer.Add(hsizer, 0, wx.EXPAND|wx.ALL, 0)
      mainsizer.Add(self.fieldpanel, 1, wx.EXPAND|wx.ALL, 0)
      self.SetSizer(mainsizer)
           
      self.Update()
      self.messagetc.Bind(wx.EVT_TEXT, self.OnMessageEnter)
      self.sendbtn.Bind(wx.EVT_BUTTON, self.OnSendMessage)

   def OnMessageEnter(self, evt):
      #print 'message enter'
      tc = evt.GetEventObject()
      msg = tc.GetValue().strip()
      msg = self._refact_msg(msg)
      self.messagetc.SetEvtHandlerEnabled(False)
      self.messagetc.SetValue(msg)
      self.messagetc.SetEvtHandlerEnabled(True)
      #print msg
      if not msg:
         return
      try:
         self.msg = Pos3Msg(msg)
      except Exception, e:
         print e
         return
      #print "Parse success"
      self.frame.reader.SetValue(self._print_fields(self.msg))
      self.fields = self.ReadFields(self.msg)
      self.vsizer.Clear(True)
      self.AddField()
   
   def _refact_msg(self, msg):
      re_wireshark = re.compile('(\w\w\:+)+\w\w$')
      re_prefix = re.compile('\[.*\]', re.DOTALL)
      if re_wireshark.match(msg):
         msg = msg.replace(':', '')
      else:
         lines = msg.splitlines()
         newline = ''
         for line in lines:
            prefix = ' '
            if re_prefix.match(line):
               prefix = re_prefix.match(line).group()
            newline += line.replace(prefix, '')      
         msg = newline.replace(' ', '')
      return msg
         
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
   
   def ReadFields(self, msg, prefix=''):
      fields = []
      prefix = '' if prefix == 'content.' else prefix
      for k in msg.fields.keys():
         if msg.getShowFlag(k):
            fields.append(prefix + msg.getName(k))
            if isinstance(msg.getField(k), Pos3MsgBase):
               fields.extend(self.ReadFields(msg.getField(k), prefix=prefix+msg.getName(k)+'.'))
      return fields
   
   def AddField(self):
      pcb = wx.ComboBox(self.fieldpanel, -1, '', choices=self.fields)
      ptc = wx.TextCtrl(self.fieldpanel, -1, '')
      pcb.ptc = ptc
      ptc.pcb = pcb
      space = 5
      hsizer = wx.BoxSizer(wx.HORIZONTAL)
      hsizer.Add(pcb, 0, wx.EXPAND|wx.ALL, space)
      hsizer.Add(ptc, 1, wx.EXPAND|wx.ALL, space)
      self.vsizer.Add(hsizer, 0, wx.EXPAND|wx.ALL, 0)
      self.fieldpanel.GetSizer().Layout()
      self.GetSizer().Layout()
      
      pcb.Bind(wx.EVT_TEXT, self.OnFieldChange)
      ptc.Bind(wx.EVT_TEXT, self.OnValueChange)
      
      self.lastpcb = pcb
      self.fieldpanel.SetupScrolling(scrollToTop=False)
      self.fieldpanel.ScrollLines(5)
      
   def OnFieldChange(self, evt): 
      pcb = evt.GetEventObject()
      value = self.msg.getField(pcb.GetValue())
      value = str(map(str, list)) if isinstance(value, list) else str(value)
      pcb.ptc.SetValue(value)
      if self.lastpcb.GetValue().strip() != '':
         self.AddField()
      
   def OnValueChange(self, evt):
      ptc = evt.GetEventObject()
      value = ptc.GetValue().strip()
      if value:
         if value.startswith('['):
            value = eval(value)
         self.msg.setField(ptc.pcb.GetValue(), value)
         self.messagetc.SetEvtHandlerEnabled(False)
         try:
            self.messagetc.SetValue(self.msg.constructMsg())
         finally:
            self.messagetc.SetEvtHandlerEnabled(True)
      
   def OnSendMessage(self, evt):
      if self.autoid:
         #TODO: Update Id by sending check in message
         msg = self.messagetc.GetValue().strip()
      else:
         msg = self.messagetc.GetValue().strip()      
      if not msg:
         return
      self.frame.start_logging()
      self.sendbtn.Enable(False)
      try:
         msgclient = PosLibrary()
         msgclient.connect_test_server('172.20.5.200', '8569', 'tcp')
         msgclient._send_receive_msg(msg)
         recv = msgclient.currentmsg
         self.frame.reader.SetValue(recv + '\n\n' + self._print_fields(recv))
      finally:
         self.sendbtn.Enable(True)
         self.frame.stop_logging()
      
   def _update_voucherNumber(self):
      #TODO: implement this
      checkmsg = self.frame.templatepanel.templatemap['TEMPLATE_POSCHECKIN_1']
      
      pass
      
   def Clear(self):
      self.messagetc.SetValue('')
      self.vsizer.Clear(True)
      self.Update()

class SSHTc(wx.TextCtrl):
   def __init__(self, parent, serverip, user, passwd, logcmd):
      wx.TextCtrl.__init__(self, parent, -1, '', style=wx.TE_MULTILINE)
      self.SetFont(Courier_New(8))
      self.ts = None
      self.serverip = serverip
      self.user = user
      self.passwd = passwd
      self.logcmd = logcmd
      self.logflag = False
      
   def start_logging(self):
      self.clear_log()
      self.ts = SSHClient(self.serverip)
      self.ts.login(self.user, self.passwd)
      self.ts.set_prompt('#')
      self.ts.write(self.logcmd)
      self.logflag = True
      threading.Thread(target=self._log_thread, args=()).start()
      
   def _log_thread(self):
      while self.logflag:
         data = self.ts.shell.recv(1000)
         if data:
            self.AppendText(data)
         else:
            time.sleep(0.5)
   
   def stop_logging(self):
      def _stop_thread():      
         time.sleep(5)
         self.logflag = False
         self.ts.close_connection()
      threading.Thread(target=_stop_thread, args=()).start()
      
   def clear_log(self):
      self.SetValue('')
      
class TemplatePanel(wx.Panel):
   def __init__(self, parent, id=-1, frame=None):
      wx.Panel.__init__(self, parent, id)
      self.frame = frame
      
      self.searchctrl = wx.SearchCtrl(self, size=(200,-1), style=wx.TE_PROCESS_ENTER)
      self.searchctrl.ShowSearchButton(True)
      self.searchctrl.ShowCancelButton(True)
      
      self.read_templates()
      self.indexlb = wx.ListBox(self, -1, style=wx.LB_SINGLE)
      self.indexlb.SetItems([' '+item for item in self.templatemap.keys()])
      self.indexlb.GetStringSelection = lambda:wx.ListBox.GetStringSelection(self.indexlb).strip()
      self.indexlb.SetFont(Courier_New())
      
      space = 5
      vsizer = wx.BoxSizer(wx.VERTICAL)
      vsizer.Add(self.searchctrl, 0, wx.EXPAND|wx.ALL, space)
      vsizer.Add(self.indexlb, 1, wx.EXPAND|wx.ALL, space)
      
      self.SetSizer(vsizer)
      
      self.indexlb.Bind(wx.EVT_LISTBOX_DCLICK, self.OnFunctionDClick)
      self.searchctrl.Bind(wx.EVT_TEXT, self.OnSearch)
      self.searchctrl.Bind(wx.EVT_SEARCHCTRL_CANCEL_BTN, self.OnSearchCancelBtn)
   
   def read_templates(self):
      path = '../../TestCase/Trade/MessageTemplate.txt'
      values = fixdict()
      with open(path, 'rb') as fp:
         lines = fp.readlines()
      for line in lines:
         if line.startswith('|'):
            _, k, v = line.split('|')
            k = k.strip()[2:-1]
            values[k] = v.strip()
      self.templatemap = values
            
   def OnFunctionDClick(self, evt):
      if isinstance(evt, basestring):
         cn = evt
      else:
         cn = self.indexlb.GetStringSelection()
      
      msgbuilder = self.frame.builder
      msgbuilder.messagetc.SetValue(self.templatemap[cn])
      
   def OnSearch(self, evt):
      sk = self.searchctrl.GetValue().strip()
      if sk:
         matchlist = []
         if sk.count('*') == 0:
            for c in self.templatemap.keys():
               if sk in c:
                  matchlist.append(c)
         else:
            sk = sk.replace('*', '.*')
            for c in self.templatemap.keys():
               if re.match(sk, c):
                  matchlist.append(c)
         self.indexlb.SetItems(matchlist)
      else:
         self.indexlb.SetItems([' '+item for item in self.templatemap.keys()])
         
   def OnSearchCancelBtn(self, evt):
      self.searchctrl.SetValue('')
      
Devil = PyEmbeddedImage(
   "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"
   "kwAAAABJRU5ErkJggg==")

class TestToolFrame(wx.Frame):
   def __init__(self, parent, id=-1):
      wx.Frame.__init__(self, parent, id, 'XGD Pos Message Builder By wuweihui', size = (970, 720))
      self.SetMinSize((640,480))
      self.panel = wx.Panel(self, -1)
      self.searchpage = None
      
      self.mgr = wx.aui.AuiManager()
      self.mgr.SetManagedWindow(self.panel)
      
      self.SetStatusBar(wx.StatusBar(self, -1))
      self.StatusBar.SetFieldsCount(2)
      self.StatusBar.SetStatusWidths([-2, -1])
      self.SetStatusText("wei_cloud@126.com", 1)

      self.builder = MessageBuilder(self.panel, frame=self)
      self.reader = wx.TextCtrl(self.panel, -1, '', style=wx.TE_MULTILINE|wx.TE_READONLY)
      self.templatepanel = TemplatePanel(self.panel, frame=self)
      
      self.operationnb = wx.aui.AuiNotebook(self.panel, style=wx.aui.AUI_NB_BOTTOM | wx.aui.AUI_NB_TAB_SPLIT \
                                            | wx.aui.AUI_NB_TAB_MOVE | wx.aui.AUI_NB_SCROLL_BUTTONS)
      self.operationnb.AddPage(self.templatepanel, 'Template')
      
      self.operationnb.Bind(wx.aui.EVT_AUINOTEBOOK_PAGE_CHANGED, self.OnOperationChange)
      
      self.clientnb = wx.aui.AuiNotebook(self.panel, style=wx.aui.AUI_NB_BOTTOM | wx.aui.AUI_NB_TAB_SPLIT \
                                         | wx.aui.AUI_NB_TAB_MOVE | wx.aui.AUI_NB_SCROLL_BUTTONS)
      self.clientnb.AddPage(self.reader, 'Reader')
      
      #for testing
      logtc = SSHTc(self.panel, '172.20.5.200', 'root', 'root200', 'tail -f /home/oracle/tuxsrvr/log.txt')      
      logtc.Bind(wx.EVT_KEY_DOWN, self.OnTextFind)
      self.clientnb.AddPage(logtc, '172.20.5.200')

      self.findext = wx.Panel(self.panel, style=wx.TAB_TRAVERSAL|wx.CLIP_CHILDREN)
      self.findtextctrl = wx.TextCtrl(self.findext, -1, '', size=(200, -1))
      findnextbutton = wx.Button(self.findext, -1, 'Next')
      extsizer = wx.BoxSizer(wx.HORIZONTAL)
      extsizer.Add(self.findtextctrl, 1, wx.EXPAND|wx.ALL, 5)
      extsizer.Add(findnextbutton, 0, wx.EXPAND, 5)
      self.findext.SetSizer(extsizer)
      self.findext.Fit()
      findnextbutton.Bind(wx.EVT_BUTTON, self.OnFindText)
      
      self.mgr.AddPane(self.clientnb, wx.aui.AuiPaneInfo().CenterPane().Name("Client"))
      self.mgr.AddPane(self.operationnb,
                       wx.aui.AuiPaneInfo().
         Left().Layer(2).BestSize(wx.Size(240, -1)).
         MinSize((160, -1)).
         Floatable(False).
         Caption("Operations").
         CloseButton(False).
         Name("Operations"))      
      self.mgr.AddPane(self.builder,
                       wx.aui.AuiPaneInfo().
         Bottom().Layer(2).
         CloseButton(False).BestSize(wx.Size(200, 400)).
         MinSize(wx.Size(200,300)).
         Caption("Message Builder").
         Name("builder"))
      self.mgr.AddPane(self.findext,
                       wx.aui.AuiPaneInfo().
         Right().Layer(3).Position(3).Row(3).
         Floatable(True).
         CloseButton(True).
         Float().Hide().
         Name("FindText"))
      self.mgr.Update()      
      self.mgr.SetFlags(self.mgr.GetFlags() ^ wx.aui.AUI_MGR_TRANSPARENT_DRAG)
      
      self.CreateMenu()
      self.tbicon = TransTaskBarIcon(self)
      self.Bind(wx.EVT_CLOSE, self.OnClose)
      
   def CreateMenu(self):
      self.ID_REALMODE = wx.NewId()
      self.ID_LAZYMODE = wx.NewId()
      menubar = wx.MenuBar()
      
      ID_ADDLOG = wx.NewId()
      logmenu = wx.Menu()
      logmenu.Append(ID_ADDLOG, "&Add Log", "Add Log", wx.ITEM_NORMAL)
      
      menubar.Append(logmenu, '&Log')
      
      self.SetMenuBar(menubar)
            
      self.Bind(wx.EVT_MENU, self.OnAddLog, id=ID_ADDLOG)
      
   def OnAddLog(self, evt):
      
      pass
   
   def start_logging(self):
      for i in range(self.clientnb.GetPageCount()):
         page = self.clientnb.GetPage(i)
         if isinstance(page, SSHTc):
            page.start_logging()
   
   def stop_logging(self):
      for i in range(self.clientnb.GetPageCount()):
         page = self.clientnb.GetPage(i)
         if isinstance(page, SSHTc):
            page.stop_logging()
 
   def OnTextFind(self, evt):
      print 'on text find'
      if evt.ControlDown() and evt.GetKeyCode() == 70:
         self.searchpage = evt.GetEventObject()
         self.fstartpos = self.searchpage.GetInsertionPoint()
         
         pt = self.searchpage.ClientToScreen(wx.Point(0, 0))
         self.mgr.GetPane("FindText").Show().FloatingPosition((pt.x+50, pt.y+50))
         self.mgr.Update()
         self.findtextctrl.SetFocus()
      evt.Skip()
      
   def OnFindText(self, evt):
      sk = self.findtextctrl.GetValue().lower().strip()
      if sk:
         src = self.searchpage.GetValue().lower()
         pos = src.find(sk, self.fstartpos)
         if pos != -1:
            self.searchpage.SetFocus()
            ppos = pos + src[:pos].count('\n')
            self.searchpage.ShowPosition(ppos+len(sk))
            self.searchpage.SetSelection(ppos, ppos+len(sk))
            self.fstartpos = pos + len(sk)
         else:
            if self.fstartpos == 0:
               return
            else:
               self.fstartpos = 0
      
   def OnOperationChange(self, evt):
      self.builder.Clear()
      pn = self.operationnb.GetPageText(evt.GetSelection())
      
   def OnClose(self, evt):
      self.tbicon.Destroy()
      evt.Skip()
      
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
      

class TestApp(wx.App):

   def OnInit(self):
      self.frame = TestToolFrame(None)
      self.frame.Show(True)
      return True
      
if __name__ == "__main__":
   app = TestApp(False)
   app.MainLoop()
   