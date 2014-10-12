#-*- coding: utf-8 -*-

import re
import PosMsg

class MsgAssertion():
   
   
   def field_should_be(self, msg, fieldname, expectstr):
      return msg.getField(fieldname) == expectstr
   
   def field_should_like(self, msg, fieldname, expectexp):
      if type(expectexp) == str:
         expectexp = re.compile(expectexp)
         
      return expectexp.search(msg.getField(fieldname))
   
   