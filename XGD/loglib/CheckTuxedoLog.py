#-*- coding: UTF-8 -*- 
'''
Created on 2014��9��23��

@author: Administrator
'''
'''
Created on 2014��9��23��

@author: Administrator
'''
import re
import os
import getLog
import LogHandle

class CheckTuxedoLog(object):
    
   def __init__(self):
      self.logName = []      


   def check_log(self, ResultCode, RspCode = '00', \
                serverip = '172.20.5.200', serverport = 22, \
                username = 'oracle', password = 'oracle200', \
                logFileName = 'log.txt', logPath = '/home/oracle/tuxsrvr/'):
#初始化变量
      self.RspCode = RspCode
      self.ResultCode = ResultCode
      self.RspCode = RspCode
      self.serverIP = serverip
      self.serverPort = serverport
      self.username = username
      self.password = password 
      self.serverLogFileName = os.path.join(logPath, logFileName)

      
#从服务器获取当前脚本运行的日志文件加上时间戳保存本地      
      getLog2Local = getLog.GetAndDelLog()
      localLogFileName = getLog2Local.get_log_file(self.serverIP, self.serverPort, self.username, self.password, self.serverLogFileName)
      
#删除服务器上当前的日志文件      
      getLog2Local.del_log_file(self.serverIP, self.serverPort, self.username, self.password, self.serverLogFileName)
      
#处理保存在本地的日志文件      
      log2Handle = LogHandle.LogHandle(localLogFileName)
      handleLog = log2Handle.tuxedoLog()
#       print len(handleLog)
      for eachLine in handleLog:
         self.logName.append(eachLine) 
      
      
#检查日志文件中的交易类别和交易结果状态      
#       f = os.path.join(self.filePath, self.logName)
#统计交易结果
      countRspCode = 0
#统计交易类别      
      countResultCode = 0
#       with open(self.logName, 'r') as fp:
      pattRspCode = 'RspCode \[' + self.RspCode + '\] !!!'
      for eachLine in self.logName:
         for x in eachLine:
            m = re.search(pattRspCode, x)
            if m is not None:
               countRspCode = countRspCode + 1
            pattResultCode = 'ResultCode:\'' + self.ResultCode + '\''
            n = re.search(pattResultCode, x)
            if n is not None:
               countResultCode = countResultCode + 1
      if self.RspCode == '00' and self.ResultCode == '1003':
         if countRspCode > 1 and countResultCode > 0:
            return 'Pass'
         else:
            return 'Faile'
      else:
         if countRspCode > 0 and countResultCode > 0:
            return 'Pass'
         else:
            return 'Faile'
#             raise AssertionError("")         
            
# a = CheckLog('1003', '00', 'C:\\', '20140922002.txt')
# print a.Check()          