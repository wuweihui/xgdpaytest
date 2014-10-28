from PerRunner import PerRunner
from pos import Pos
from XGD.poslib.PosMsg import Pos3Msg
from process import perCase

from robot.api import logger

def nolog(*args, **kws):
   pass
logger.debug = nolog

# class testRunner(PerRunner):
#    def __init__(self):
#       PerRunner.__init__(self)
#       self.testfunc = self.myfunc
#       
#    def myfunc(self):
#       pos = Pos()
#       pos.connect_test_server('172.20.5.200', '8569', 'tcp')
#       pos.set_field('cardno', '6226160600005000')
#       pos.set_field('operationData.tradeAmount', '000000003333')
#       pos.load_template('TEMPLATE_POSTRADE', terminalId='3830303134303939', merchantId='383439343430333533313136303331')
#       ret = pos.send_pos_message()
#       msg = Pos3Msg(ret)
#       if msg.getField('operationData.showReultMsg.responseCode') != '3030':
#          raise AssertionError("Response code not correct: %s" % msg.getField('operationData.showReultMsg.responseCode'))

def testrun():
   idlist = [['3830303134303939', '383439343430333533313136303331']]
   fields = {'operationData.tradeAmount':'000000003333',
             'cardno':'6226160600005000'}
   testcase = perCase('trade')
   testcase.init_pos_list('172.20.5.200', '8569', 'tcp', idlist, fields)
   testcase.start()


if __name__ == '__main__':
   #testRunner().start()
   testrun()