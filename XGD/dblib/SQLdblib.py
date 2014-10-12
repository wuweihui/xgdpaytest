#-*- coding: utf-8 -*-

import time
from copy import deepcopy
import MySQLdb as db

class SQLdblib():
   def __init__(self):      
      self.conn = None
      self.cursor = None
   
   def connect_to_db(self, host, port, user, passwd, db, charset='utf8'):
      conn = db.connect(host=host, port=port, user=user, passwd=passwd, db=db, charset=charset)
      self.conn = conn
      self.cursor = conn.cursor()
   
   def execute_sql(self, sql):
      if not self.cursor:
         raise RuntimeError("Connect to db first!")         
      return self.cursor.execute(sql)
   
   def execute_batch_sql(self, sqllist):
      if not self.cursor:
         raise RuntimeError("Connect to db first!")
      for sql in sqllist:
         self.execute_sql(sql)
         
   def disconnect_from_db(self):
      if self.cursor:
         self.cursor.close()
      if self.conn:
         self.conn.close()
      self.conn = None
      self.cursor = None