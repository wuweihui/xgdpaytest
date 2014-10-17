#-*- coding: UTF-8 -*- 

'''
Created on 2014��9��25��

@author: Administrator
'''

from re import search

class LogHandle():
   
   def __init__(self,logFileName = 'd:\\tuxedoLog\\tuxedolog.txt'):
      self.logName = logFileName
      
#定义正则表达式，按列拆分日志文件      
   def tuxedoLog(self):
      pattern = '(\[\d{2}/\d{2} \d{2}\:\d{2}\:\d{2}\.\d{3}\])(\[\w+\]|\[\w+_\w+\])(\[[A-Z]{3}\])(\[\d+\])(\[\w+\.\w+\:\w+\:\d+\]|\[\s+\d+\])([\s\S]*)'
      n = []
      with open(self.logName,'r') as f:
         for eachLine in f:
            x = eachLine.strip()
            m = search(pattern, x)
            if m is not None:
               n.append(m.groups())
      return n
   
   def callback(self, func = 'None'):
      n = LogHandle.tuxedoLog()
      if func != 'None':
         return func(n)
      else:
         return n
   
#   print n[0]
# m = LogHandle('C:\\','20140922002.txt')
# print(m.tuxedoLog())
