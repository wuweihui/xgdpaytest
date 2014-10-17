#-*- coding: UTF-8 -*- 
'''
Created on 2014��9��25��

@author: Administrator
'''



import paramiko
import datetime

class GetAndDelLog():
      
   def get_log_file(self,serverip = '172.20.5.200', port = 22, username = 'oracle', password = 'oracle200', logFileName = '/home/oracle/tuxsrvr/log.txt'):
      self.serverip = serverip
      self.port = port
      self.username = username
      self.password = password
      self.serverLogFilename = logFileName     
      
      time = ((datetime.datetime.now()).strftime("%Y%m%d%H%M%S")+str((datetime.datetime.now()).microsecond/1000))
      localLogFileName = 'D:\\tuxedo' + time + '.txt'
      try:
         t = paramiko.Transport(self.serverip, self.port)
         t.connect(username=self.username, password=self.password)
         sftp = paramiko.SFTPClient.from_transport(t)
         #   sftp.put('C:\\20140922002.txt', '/home/zhangkai/py_test/to/20140922002.txt')
         #   sftp.get('/home/zhangkai/py_test/to/20140922002.txt', 'D:\\20140922002.txt')
         sftp.get(self.serverLogFilename, localLogFileName)   
         t.close();
      except Exception, e:
            import traceback
            traceback.print_exc()
            try:
               t.close()
            except:
               pass
      return localLogFileName            
            
   def del_log_file(self,serverip = '172.20.5.200', port = 22, username = 'oracle', password = 'oracle200', logFileName = '/home/oracle/tuxsrvr/log.txt'):            
      s=paramiko.SSHClient()                 
      s.set_missing_host_key_policy(paramiko.AutoAddPolicy())          
      s.connect(hostname = serverip,port=port,username=username, password=password)          
      s.exec_command('rm -rf ' + logFileName)          
      s.close()
      
       
#    def delLogFile(self):


# m = GetLog()
# s = m.getLogFile()
# print s
# m.delLogFile()          
