#-*- coding: utf-8 -*-
from PosMsg import *
from pos3client import *
import random
from robot.api import logger
import re


class PosLibrary(object):
   
   def __init__(self):
      self.client = Pos3Client()
      self.currentmsg = ''
      self.voucherNo = ''
      self.batchNo = ''
      self.protocol = None            
      self.fields = {}
      
   def connect_test_server(self, host, port, protocol=TCP_PROTOCOL):
      self.host = host
      self.port = int(port)
      self.protocol = protocol
      logger.debug("host:%s, port:%s, protocol%s" %(host, port, protocol))
   
   def send_pos_message(self, template, *args, **kws):
      msg = Pos3Msg(template)
      
      for arg in args:
         if arg.count('=') == 1:
            k, v = arg.split('=')
            kws[k] = v
      kws.update(self.fields)
      for k, v in kws.items():
            msg.setField(k, v)
            
      if not kws or 'voucherNo' not in kws.keys():
         msg.setField('voucherNo', self._get_next_voucherNo())
      
      if self.batchNo and (not kws or 'batchNo' not in kws.keys()):
         msg.setField('batchNo', self.batchNo)
       
      if not kws or 'transactionRandId' not in kws.keys():
         msg.setField('transactionRandId', self.generate_transactionRandId())
                   
      packet = msg.constructMsg()
      ret = self._send_receive_msg(packet)
      self.fields={}
      return ret
   
   def generate_transactionRandId(self):
      """
      'transactionRandId', ':', 'c1eeab7c'
      """
      randid = ''
      choices = ['0','1','2','3','4','5','6','7','8','9','a','b','c','d','e','f']
      for i in range(0, 8):
         randid += random.choice(choices)
      
      return randid
   
   def _gernerate_syncSerialNumber(self):
      """
      'syncSerialNumber', ':', '03'
      """
      randid = ''
      choices = ['0','1','2','3','4','5','6','7','8','9','a','b','c','d','e']
      for i in range(0, 2):
         randid += random.choice(choices)
      
      return randid
   
   def set_field(self, fieldId, value):
      """
      operationData.cardReadOrderResult.validData=6226160600005000358dc1f7680229b594235c5e3b66cad0
      """
      if fieldId.lower() == 'cardno':
         #358dc1f7680229b594235c5e3b66cad0
         self.fields['operationData.cardReadOrderResult.validData'] = value + '358dc1f7680229b594235c5e3b66cad0'
      else:
         self.fields[fieldId] = value
   
   def get_field(self, fieldId):
      msg = self._get_Pos3Msg()
      return msg.getField(fieldId)

   def field_should_be(self, fieldname, expectstr):
      msg = self._get_Pos3Msg()
      if msg.getField(fieldname) != expectstr:
         raise AssertionError("Field value not equal! %s:%s expected:%s" %(fieldname, msg.getField(fieldname), expectstr))
   
   def field_should_like(self, fieldname, expectexp):
      if type(expectexp) == str:
         expectexp = re.compile(expectexp)      
      msg = self._get_Pos3Msg()
      ret = expectexp.search(msg.getField(fieldname))
      if not ret:
         raise AssertionError("Field value not equal! %s:%s expected:%s" %(fieldname, msg.getField(fieldname), expectstr))
   
   def field_should_contain(self, fieldname, expectstr):
      msg = self._get_Pos3Msg()
      if expectstr not in msg.getField(fieldname):
         raise AssertionError("Field value not equal! %s:%s expected:%s" %(fieldname, msg.getField(fieldname), expectstr))

   def field_should_not_be(self, fieldname, expectstr):
      msg = self._get_Pos3Msg()
      if msg.getField(fieldname) == expectstr:
         raise AssertionError("Field value not equal! %s:%s expected:%s" %(fieldname, msg.getField(fieldname), expectstr))
   
   def field_should_not_like(self, fieldname, expectexp):
      if type(expectexp) == str:
         expectexp = re.compile(expectexp)      
      msg = self._get_Pos3Msg()
      ret = expectexp.search(msg.getField(fieldname))
      if ret:
         raise AssertionError("Field value not equal! %s:%s expected:%s" %(fieldname, msg.getField(fieldname), expectstr))
   
   def field_should_not_contain(self, fieldname, expectstr):
      msg = self._get_Pos3Msg()
      if expectstr in msg.getField(fieldname):
         raise AssertionError("Field value not equal! %s:%s expected:%s" %(fieldname, msg.getField(fieldname), expectstr))

   def operation_codes_should_be(self, codelist):
      msg = self._get_Pos3Msg()
      opcodes = msg.getField('operationCode').opcodes
      if len(codelist) != len(opcodes):
         raise AssertionError("Operation codes not equal! %s expected:%s" %(str([i.codenumber for i in opcodes]), str(codelist)))
      
      for i in range(len(codelist)):
         if int(codelist[i]) != opcodes[i].codenumber:
            raise AssertionError("Operation codes not equal! %s expected:%s" %(str([i.codenumber for i in opcodes]), str(codelist)))
   
   def _send_receive_msg(self, msg):
      self.client.connect_to_server(self.host, self.port, self.protocol)
      self.currentmsg = self.client.send_receive(msg)
      self.client.close_connection()
      return self.currentmsg
   
   def close_connection(self):
      self.client.close_connection()
      
   def _get_next_voucherNo(self):
      if self.voucherNo.lower() == 'ffffff':
         self.voucherNo = '1'
      elif not self.voucherNo:
         self.voucherNo = '1'
      else:
         try:
            self.voucherNo = str(int(self.voucherNo)+1)
         except:
            self.voucherNo = str(int(self.voucherNo, 16)+1)
      return self.voucherNo
   
   def update_voucher_number(self):
      if self.currentmsg:
         self.voucherNo = self._get_Pos3Msg().getField('voucherNo')
         self.batchNo = self._get_Pos3Msg().getField('batchNo')
      else:
         pass
   
   def _get_Pos3Msg(self):
      if self.currentmsg and isinstance(self.currentmsg, basestring):
         self.currentmsg = Pos3Msg(self.currentmsg)
      return self.currentmsg
   
   def convert_int_to_bcd(self, base, force=True):
      re_bcd = re.compile('(3\d)+$')
      if not force and re_bcd.match(str(base)):
         return str(base)
      else:
         return ''.join(['3'+i for i in list(str(base))])

   def convert_bcd_to_int(self, base, force=True):
      re_bcd = re.compile('(3\d)+$')
      if force or re_bcd.match(str(base)):
         return base[1::2]
      else:
         return str(base)