import re

class xgdlogbase(object):
   
   def __init__(self, log):
      self.time = ''
      self.module = ''
      self.level = ''
      self.id = ''
      self.codefile = ''
      self.funcname = ''
      self.linenum = ''
      self.content = ''
      self.extra = ''
      self._parse(log)
      
   def _parse(self, log):
      """
      """
      re_baseline = re.compile(r'''\[(?P<time>\d\d\/\d\d\s\d\d\:\d\d\:\d\d\.\d\d\d)\]
                                   \[(?P<module>\w+?)\]
                                   \[(?P<level>\w+?)\]
                                   \[(?P<id>\d+)\]
                                   \[(?P<codefile>\w+\.\w+)\:(?P<funcname>\w+)\:(?P<linenum>\d+)\]
                                   \s+(?P<content>.*)''', re.X)
      re_extra = re.compile(r'''\[(?P<time>\d\d\/\d\d\s\d\d\:\d\d\:\d\d\.\d\d\d)\]
                                   \[(?P<module>\w+?)\]
                                   \[(?P<level>\w+?)\]
                                   \[(?P<id>\d+)\]
                                   \[(?P<seq>\s*\d+)\]
                                   \s+(?P<content>.*)''', re.X)
      if isinstance(log, list):
         lines = log
      else:
         lines = log.splitlines()
      for line in lines:
         m = re_baseline.match(line)
         if m:
            ret = m.groupdict()
            self.time, self.module, self.level, self.id, self.codefile, self.funcname, self.linenum = \
            ret['time'], ret['module'], ret['level'], ret['id'], ret['codefile'], ret['funcname'], ret['linenum']
            self.content = ret['content']
         else:
            m = re_extra.match(line)
            if m:
               ret = m.groupdict()
               if not self.content or self.id != ret['id']:
                  print('Log out of order will be discard! %s' % line)
               else:
                  self.extra += ret['content']
            else:
               print('Log format not supported! %s' % line)
               

class xgdloglistbase(list):
   def __init__(self, log):
      list.__init__(self)
      self._parse(log)
   
   def _parse(self, log):
      re_baseline = re.compile(r'''\[(?P<time>\d\d\/\d\d\s\d\d\:\d\d\:\d\d\.\d\d\d)\]
                                   \[(?P<module>\w+?)\]
                                   \[(?P<level>\w+?)\]
                                   \[(?P<id>\d+)\]
                                   \[(?P<codefile>\w+\.\w+)\:(?P<funcname>\w+)\:(?P<linenum>\d+)\]
                                   \s+(?P<content>.*)''', re.X)
      lines = []
      for line in log.splitlines():
         m = re_baseline.match(line)
         if m:
            if lines:
               self.append(xgdlogbase(lines))
            lines = [line]
         else:
            lines.append(line)

   def searchlog(self, expectstr='', time='', module='', level='', id='', codefile='', funcname=''):
      outlist = []
      for logitem in self:
         if (not expectstr or logitem.content.contains(expectstr)\
             and not time or logitem.time.contains(time)\
             and not module or logitem.module == module\
             and not level or logitem.level == level\
             and not id or logitem.id == id\
             and not codefile or logitem.codefile == codefile\
             and not funcname or logitem.funcname == funcname):
            outlist.append(logitem)
      return outlist  
      
if __name__ == '__main__':
   with open('testlog.txt', 'rb') as fp:
      log = fp.read()
   
   loglist = xgdloglistbase(log)
   for item in loglist:
      print item.id, item.content