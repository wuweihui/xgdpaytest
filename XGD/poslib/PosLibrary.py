#-*- coding: utf-8 -*-
import MsgTemplate
from PosMsg import *
from pos3client import *
import random
from robot.api import logger


class PosLibrary():
   
   def __init__(self):
      self.client = Pos3Client()
      self.currentmsg = ''
      self.tradeseq = ''      
      self.protocol = None
      
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
      for k, v in kws.items():
            msg.setField(k, v)
            
      if not kws or 'tradeSeq' not in kws.keys():
         msg.setField('tradeSeq', self._get_next_tradeseq())
      
      if not kws or 'transactionRandId' not in kws.keys():
         msg.setField('transactionRandId', self.generate_transactionRandId())
         
      packet = msg.constructMsg()
      ret = self._send_receive_msg(packet)
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
      msg = Pos3Msg(self.currentmsg)
      ret = expectexp.search(msg.getField(fieldname))
      if not ret:
         raise AssertionError("Field value not equal! %s:%s expected:%s" %(fieldname, msg.getField(fieldname), expectstr))
   
   def field_should_contain(self, fieldname, expectstr):
      msg = self._get_Pos3Msg()
      if expectstr not in msg.getField(fieldname):
         raise AssertionError("Field value not equal! %s:%s expected:%s" %(fieldname, msg.getField(fieldname), expectstr))

   def _send_receive_msg(self, msg):
      self.client.connect_to_server(self.host, self.port, self.protocol)
      self.currentmsg = self.client.send_receive(msg)
      self.client.close_connection()
   
   def close_connection(self):
      self.client.close_connection()
      
   def _get_next_tradeseq(self):
      if self.tradeseq.lower() == 'ffffff':
         self.tradeseq = '1'
      elif not self.tradeseq:
         self.tradeseq = 'ffffff'
      else:
         self.tradeseq = toHexstr(int(self.tradeseq, 16)+1)
      return self.tradeseq
   
   def update_tradeseq(self):
      if self.currentmsg:
         self.tradeseq = self._get_Pos3Msg().getField('tradeSeq')
      else:
         pass
   
   def _get_Pos3Msg(self):
      if self.currentmsg and isinstance(self.currentmsg, basestring):
         self.currentmsg = Pos3Msg(self.currentmsg)
      return self.currentmsg