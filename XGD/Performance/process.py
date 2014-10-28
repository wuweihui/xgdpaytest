#-*- coding: utf-8 -*-

from pos import Pos
from PerRunner import PerRunner
import threading
import time

class perCase(PerRunner):
   def __init__(self, processname):
      PerRunner.__init__(self)
      self.poslist = []
      self.processname = processname
      self.regist_error_code_counter()

   def init_pos_list(self, host, port, protocol='tcp', idlist=[], fields={}):
      self.poslist = []
      for tid, mid in idlist:
         fields['terminalId'] = tid
         fields['merchantId'] = mid
         pos = Pos(fields=fields)
         pos.connect_test_server(host, port, protocol)
         self.poslist.append(pos)
         
   def run(self):
      self.init_counters()
      self.runflag = True
      
      for pos in self.poslist:
         if not self.runflag:
            break
         self.testfunc = pos.__getattribute__(self.processname)
         p = threading.Thread(target = self._perfunction_thread, args = ())
         p.start()
         self.threads.append(p)
         time.sleep(self.threadinterval)
   
   def add_response_error(self, value, ret):
      try:
         k = ret.code
         if value.has_key(k):
            value[k] = value[k] + 1
         else:
            value[k] = 1
      except Exception:
         pass
      return value
         
   def regist_error_code_counter(self):
      self.regist_counter("ErrorCode", {}, self.TOT_FAILIURE, self.add_response_error)
      self.regist_counter("IntervalErrorCode", {}, self.INTERVAL_FAILIURE, self.add_response_error)
   
   