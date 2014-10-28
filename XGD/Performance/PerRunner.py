#-*- coding:utf-8 -*-
"""

(C) Copyright 2010-2015 wei_cloud@126.com

"""

import threading
import ConfigParser
import time
import random
import traceback
from exceptions import *
import StringIO

from loglib import *

class PerRunner(object):
   printlock = threading.RLock()
   counterlock = threading.RLock()
   itercounterlock = threading.RLock()
   ecounterlock = threading.RLock()
   iterecounterlock = threading.RLock()
   customlock = threading.RLock()
   
   TOT_SUCCESS = 0
   INTERVAL_SUCCESS = 1
   TOT_FAILIURE = 2
   INTERVAL_FAILIURE = 3
   
   def __init__(self, target=None, args=[], kws={}, id='', threadnum=2):
      """
      runner = PerRunner(target=testfunc)
      runner.start()
      or you can also inheritate this class and implemante the self.testfunc function
      example:
      class myRunner(PerRunner):
         def __init__(self):
            PerRunner.__init__(self)
            self.testfunc = self.myfunc
         
         def myfunc(self):
            print 'Do something here'
      runner = myRunner()
      runner.start()
      """
      self.runflag = False
      self.threads = []
      self.addtioncounters = []
      self.testfunc = target
      self.testargs = args
      self.testkws = kws
      self.id = id
      self.threadnum = threadnum        #thread number
      self.operateinterval = 1          #user operation interval
      self.threadinterval = 20.0/1000   #thread interval
      self.contime = 60                 #continiuos time
      self.printinterval = 10           #counters print interval
      
      self.init_counters()
      
   def init_counters(self):
      self.scounter = 0       #Total successfull times
      self.itercounter = 0    #Successfull times in one interval statstic time
      self.runningcounter = 0 #Session Ongoing
      self.totutime = 0       #Total time used by calling the function
      self.iterutime = 0      #Time used in one interval statstic time 
      self.ecounter = {}      #Error counter
      self.iterecounter = {}  #Interval error counter
      self._init_addtion_counter()
      
   def run(self):
      self.init_counters()
      self.runflag = True
      
      for i in range(self.threadnum):
         if not self.runflag:
            break
         p = threading.Thread(target = self._perfunction_thread, args = ())
         p.start()
         self.threads.append(p)
         time.sleep(self.threadinterval)             
      
   def _perfunction_thread(self):
      
      runtime = time.time()
      while self.runflag:          
         
         try:
            with self.counterlock:
               self.runningcounter += 1 
            stime = time.time()
            ret = self.testfunc(*self.testargs, **self.testkws)
            utime = time.time() - stime
            with self.counterlock:
               self.scounter += 1
               self.totutime += utime
            with self.itercounterlock:
               self.itercounter += 1
               self.iterutime += utime
            self._handle_addtion_counter(ret=ret)
         except Exception, e:
            if isinstance(e, NameError):
               buf = StringIO.StringIO()
               traceback.print_exc(file=buf)
               logerr(buf.getvalue())
            key = str(e.__class__)
            with self.ecounterlock:
               self.ecounter[key] = self.ecounter.has_key(key) and self.ecounter[key]+1 or 1
            with self.iterecounterlock:
               self.iterecounter[key] = self.iterecounter.has_key(key) and self.iterecounter[key]+1 or 1
            self._handle_addtion_counter(e=e)
         with self.counterlock:
               self.runningcounter -= 1 
         
         if self.contime and (time.time() - runtime) > self.contime:    #finished
            break    
         
         time.sleep(self.operateinterval)
      
   def regist_counter(self, name, initvalue, ctype, handle=None):
      """
      example:
      regist_counter('intervallen', 0,
                     ctype = PerRunner.INTERVAL_SUCCESS, 
                     handle = lambda value, ret: ret and value+len(ret) or value)
      """
      new_counter =  percounter(name, initvalue, ctype, handle)
      self.addtioncounters.append(new_counter)
      
   def _handle_addtion_counter(self, ret=None, e=None, interval=None):
      for addtion_counter in self.addtioncounters:         
         if ret and (addtion_counter.type == self.TOT_SUCCESS or addtion_counter.type == self.INTERVAL_SUCCESS):
            with self.customlock:
               addtion_counter.add(ret)
         elif e and (addtion_counter.type == self.TOT_FAILIURE or addtion_counter.type == self.INTERVAL_FAILIURE):
            with self.customlock:
               addtion_counter.add(e)
         elif interval and (addtion_counter.type == self.INTERVAL_FAILIURE or addtion_counter.type == self.INTERVAL_SUCCESS):
            with self.customlock:
               addtion_counter.refresh()
   
   def _init_addtion_counter(self):
      for addtion_counter in self.addtioncounters:
         addtion_counter.refresh()
   
   def _log_addtion_counter(self):
      for addtion_counter in self.addtioncounters:
         log(addtion_counter.name, '=', addtion_counter.value)  
      
   def refresh_interval_counter(self):
      with self.itercounterlock:
         self.iterutime = 0
         self.itercounter = 0
      with self.iterecounterlock:
         self.iterecounter = {}
      self._handle_addtion_counter(interval=True)
   
   def _print_thread(self, refresh=False):
      '''
      '''
      while self.runflag:
         self.print_counters(refresh)
      
         time.sleep(self.printinterval) 
         
   def print_counters(self, refresh=False):
      '''
      self.scounter = 0       #Total successfull times
      self.itercounter = 0    #Successfull times in one interval statstic time
      self.totutime = 0       #Total time used by calling the function
      self.iterutime = 0      #Time used in one interval statstic time 
      self.ecounter = {}      #Error counter
      self.iterecounter = {}  #Interval error counter
      '''
      log('*'*30)
      log('Total Success:', self.scounter) 
      if self.scounter > 0:
         log('Average Time Delay:', self.totutime/self.scounter)
      log('Total Failure:', sum(self.ecounter.values()))
      log(**self.ecounter)
     
      log('Interval Success:', self.itercounter)
      if self.itercounter > 0:
         log('Interval Time Delay:', self.iterutime/self.itercounter)
      log('Interval Failure:', sum(self.iterecounter.values()))
      log(**self.iterecounter)
      self._log_addtion_counter()          
      if refresh:
         self.refresh_interval_counter()
         
   def get_counters():
       """
       return the counter list
       [(name, value), ...]
       order
       [TOT Success, TOT Error, TOT Delay, INTER Success, INTER Delay, INTER Error, Additional Counters]
       """
       counters = []
       counters.append(("TOT Success", self.scounter))          
       counters.append(("TOT Error", self.ecounter))
       counters.append(("TOT Delay", self.totutime))    
       counters.append(("INTER Success", self.itercounter))
       counters.append(("INTER Delay", self.iterutime))
       counters.append(("INTER Error", self.iterecounter))
              
       for addtion_counter in self.addtioncounters:
          counters.append((addtion_counter.name, addtion_counter.value))
          
       return counters
      
   def start(self):
      """
      start performance testing, 
      this function could be used in the console mode
      """      
      self.runflag = True
      pr = threading.Thread(target = self._print_thread, args = (True,))
      pr.start()
      p = threading.Thread(target = self.run, args = ())
      p.start()
      
      try:
         p.join()
         self.join()
      finally:         #catch the keyboard interrupt and stop the print thread
         self.runflag = False
         pr.join()
      
   def start_ex(self):
      """
      Running the test without printing
      This function could be used in the wx mode
      This function is not quite safe, should use self.run instead
      """
#      self.runflag = True
#      p = threading.Thread(target = self.run, args = ())
#      p.start()
      self.runflag = True
      self.run()      
      log('***** All thread is running now *****')
      self.join()
      
   def stop(self):
      self.runflag = False
      self.join()
   
   def join(self):
      for p in self.threads:
         p.join()
      
   def is_alive(self):
      return True in map(threading.Thread.is_alive, self.threads)
      
   def active_count(self):
      return map(threading.Thread.is_alive, self.threads).count(True)
   
   def set_config_file(self, path):
      """
      Read configueration from a file.
      file content should be in the format like bellow:
      [options]
      threadnum = 20
      operateinterval = 1
      threadinterval = 0.02
      contime = 60      
      printinterval = 10
      """
      config = ConfigParser.RawConfigParser()
      config.read('path')
      
      self.threadnum = config.getint('options', 'threadnum')               
      self.operateinterval = config.getfloat('options', 'operateinterval')             
      self.threadinterval = config.getfloat('options', 'threadinterval')  
      self.contime = config.getint('options', 'contime')     
      self.printinterval = config.getint('options', 'printinterval')               
      

class percounter(object):
   def __init__(self, name, initvalue, ctype, handle=None):
      """
      handle function should take two arguments, 
      (current_value, counter_source)
      and returns the new value.
      the source could be the test function return value or error message
      """
      self.name = name
      self.initvalue = initvalue
      self.type = ctype
      self.handle = handle 
      self.value = self.initvalue
   
   def refresh(self):
      self.value = self.initvalue
      
   def add(self, arg=None):
      if self.handle:
         self.value = self.handle(self.value, arg)
      elif isinstance(self.value, int) or isinstance(self.value, long):
         self.value += 1
      else:
         pass
   
   def get_value(self):
      return self.value
   
   def __str__(self):
      return self.value.__str__()
         
class Waiter:
    
    def __init__(self, time):
        pass
    
    def start(self):
        pass
    
    def stop(self):
        pass
      
#
#def testprint():
#   ret = random.randint(22,2032)
#   if ret < 500:
#      1/0
#   if ret <1000:
#      print asjdflkja
#   return True
#   
#
#def add_test(value):
#   return value + 10

#if __name__ == '__main__':
#   ta = PerRunner(target=testprint, id="test script", threadnum=50)
#   ta.regist_counter('intervallen', 0,
#                     ctype = ta.INTERVAL_SUCCESS,
#                     handle = lambda value, ret: ret and add_test(value) or value)
#                     #handle = None)
#   ta.start()