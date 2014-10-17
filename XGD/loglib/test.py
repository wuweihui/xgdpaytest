#-*- coding: UTF-8 -*- 
'''
Created on 2014��9��25��

@author: Administrator
'''

# import getLog
# import LogHandle
import CheckTuxedoLog


# m = getLog.GetLog()
# n = m.getAndDelLogFile()
# # for eachLine in n:
# #    print (eachLine)
# print n
# o = LogHandle.LogHandle(n)
# p = o.tuxedoLog()
# print len(p)
# # for eachLine in p:
# #    print (eachLine)
# q = CheckTuxedoLog.CheckTuxedoLog(p,'1000','00')
# print(q.CheckLog())

m = CheckTuxedoLog.CheckTuxedoLog()
print(m.check_log('1000','00','172.20.5.200',22,'oracle','oracle200','log.txt','/home/oracle/tuxsrvr/'))