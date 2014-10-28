#-*- coding: utf-8 -*-
from XGD.poslib.PosMsg import *
from XGD.poslib.pos3client import *
from XGD.poslib.PosLibrary import PosLibrary
import random
from robot.api import logger
import re


class ResponseCodeError(AssertionError):
   def __init__(self, code, *args, **kws):
      AssertionError.__init__(self, *args, **kws)
      self.code = code

class Pos(PosLibrary):
   
   def __init__(self, fields={}):
      PosLibrary.__init__(self)
      self.checkedin = False
      self.sendmsg = ''
      self.kws = fields
      if self.kws.has_key('cardno'):
         v = self.kws.pop('cardno')
         self.kws['operationData.cardReadOrderResult.validData'] = v + '358dc1f7680229b594235c5e3b66cad0'
      self.read_templates()
      
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
      
   def load_template(self, template, *args, **kws):
      msg = Pos3Msg(self.templatemap[template])
      
      for arg in args:
         if arg.count('=') == 1:
            k, v = arg.split('=')
            kws[k] = v
      kws.update(self.fields)
      for k, v in kws.items():
            msg.setField(k, v)
            
      if not self.checkedin and template not in ['TEMPLATE_POSCHECKIN_1', 'TEMPLATE_POSCHECKIN_2']:
         self.check_in()
            
      if not kws or 'voucherNo' not in kws.keys():
         msg.setField('voucherNo', self._get_next_voucherNo())
      
      if self.batchNo and (not kws or 'batchNo' not in kws.keys()):
         msg.setField('batchNo', self.batchNo)
       
      if not kws or 'transactionRandId' not in kws.keys():
         msg.setField('transactionRandId', self.generate_transactionRandId())
                   
      self.sendmsg = msg.constructMsg()
      logger.debug('===Sending Message:'+self.sendmsg)
      return self.sendmsg
   
   def check_in(self):
      """
      """
      origfields = self.fields
      self.fields = {}
      randid = self.generate_transactionRandId()      
      self.load_template('TEMPLATE_POSCHECKIN_1', terminalId=self.kws['terminalId'], merchantId=self.kws['merchantId'], transactionRandId=randid)
      self.send_pos_message()
      self.update_voucher_number()      
      self.load_template('TEMPLATE_POSCHECKIN_2', terminalId=self.kws['terminalId'], merchantId=self.kws['merchantId'], transactionRandId=randid)
      self.send_and_check_response()      
      self.fields = origfields
      self.checkedin = True
   
   def send_pos_message(self):      
      ret = self._send_receive_msg(self.sendmsg)
      self.fields={}
      return ret
   
   def send_and_check_response(self, expect='3030'):
      ret = self.send_pos_message()
      msg = Pos3Msg(ret)
      if msg.getField('operationData.showReultMsg.responseCode') != expect:
         raise ResponseCodeError(msg.getField('operationData.showReultMsg.responseCode'), "Response code not correct")
   
   def trade(self):
      self.load_template('TEMPLATE_POSTRADE', **self.kws)
      print self.sendmsg
      self.send_and_check_response()
      
   def trade_cancel(self):
      self.trade()
      vouch = self.convert_int_to_bcd(self.get_field('voucherNo'))
      args = ['operationData.searchOriginalTradeResult.searchResult='+vouch]
      self.load_template('TEMPLATE_POSTRADECANCEL', *args, **self.kws)
      self.send_and_check_response()
      
   def query(self):
      self.load_template('TEMPLATE_POSINQUIRY', **self.kws)
      self.send_and_check_response()
      
   def preauth(self):
      self.load_template('TEMPLATE_PREAUTH', **self.kws)
      self.send_and_check_response()
   
   def preauth_cancel(self):
      self.preauth()
      authnumber = self.get_field('operationData.saveTradeList.recordList')[0].authNumber
      readdate = self.get_field('operationData.saveTradeList.recordList')[0].tradeTime[:8]  
          
      args = ['operationData.searchOriginalTradeResult.searchResult='+authnumber, 'readDate='+readdate]
      self.load_template('TEMPLATE_PREAUTHCANCEL', *args, **self.kws)
      self.send_and_check_response()
      
   def trade_correction(self):
      if not self.kws.has_key('MAC'):
         self.kws['MAC'] = '969b9a4a20f19a63'
      self.load_template('TEMPLATE_POSTRADE', **self.kws)
      self.send_and_check_response()
      vouch = self.get_field('voucherNo')
      args = ['operationData.searchOriginalTradeResult.searchResult='+vouch, 'operationData.correctionMsg.tradeMAC='+self.kws['MAC']]
      self.load_template('TEMPLATE_POSTRADECANCEL', *args, **self.kws)
      self.send_and_check_response()
      
   def preauth_complete(self):
      self.preauth()
      authnumber = self.get_field('operationData.saveTradeList.recordList')[0].authNumber
      readdate = self.get_field('operationData.saveTradeList.recordList')[0].tradeTime[:8]  
          
      args = ['operationData.searchOriginalTradeResult.searchResult='+authnumber, 'readDate='+readdate]
      self.load_template('TEMPLATE_PREAUTHCOMPLETE', *args, **self.kws)
      self.send_and_check_response()
   
   def preauth_complete_cancel(self):
      self.preauth_complete()
      vouch = self.convert_int_to_bcd(self.get_field('voucherNo'))
      args = ['operationData.searchOriginalTradeResult.searchResult='+vouch]
      self.load_template('TEMPLATE_PREAUTHCANCELCOMPLETE', *args, **self.kws)
      self.send_and_check_response()
      
   