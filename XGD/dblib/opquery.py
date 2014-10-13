# -*- coding: utf-8 -*-

from robot.api import logger

class OPQuery(object):
   
   def connect_op_system(self, system, dbType, dbName):
      self.set_op_system(system)
      connect_to_database(self, dbapiModuleName=dbType, dbName=dbName, \
                          dbUsername=self.dbUser, dbPassword=self.dbPawd, \
                          dbHost=self.dbHost, dbPort=self.dbPort, dbConfigFile="./resources/db.cfg")
   
   def set_op_system(self, system):
      self.confFile = "dbinfo_%s.txt" % self.system 
      self._init_op_system()
   
   def _init_op_system(self):
      file = open(self.confFile)
      for line in file:
         params = line.strip().split();
         #oracle      172.17.5.67   jydb      trade_mpay   trade123
         if len(params)!=5:
            continue
         if params[0]==self.dbType and params[2]==self.dbName:
            self.dbHost = params[1].split(':')[0]
            self.dbPort = 0 if len(params[1].split(':'))<2 else params[1].split(':')[1]
            self.dbUser = params[3]
            self.dbPawd = params[4]
            return True
        
   def getDBOperationInfo(self,opTpye):
      file = open(self.confFile)
      sql = ''
      for line in file:
         params = line.strip().split();
         #query      select * from t_trade_order
         if len(params)<2:
            continue
         if params[0]==opTpye and params[2] != None:
            for i in range(1,len(params)):
               sql += params[i] + ' '
      file.close()
      return sql.strip()
   
   def getBatchDBOperationInfo(self,prestring):
      file = open(self.confFile)
      list_sql = []
      for line in file:
         params = line.strip().split();
         #query      select * from t_trade_order
         if len(params)<2:
            continue
         if params[0].find(prestring)==0 and params[2] != None:
            sql = ''
            for i in range(1,len(params)):
               sql += params[i] + ' '
            list_sql.append(sql.strip())
      file.close()
      return list_sql
   
   def opquery(self,opType,params = None):
   #查询
      '''
               查询：按配置 文件
      '''
      dbSql = self.getDBOperationInfo(opType)
      if dbSql=='':
         raise RuntimeError('ERROR:get db opreation info error,not exist the DB:%s %s' %(self.system,opType))
      if params != None:
         dbSql = dbSql % params
      return self.query(dbSql)
   
   def opquery_one(self,opType,params = None):
   #查询--返回第一条数据
      '''
               查询：按配置 文件
      '''
      dbSql = self.getDBOperationInfo(opType)
      if dbSql=='':
         raise RuntimeError('ERROR:get db opreation info error,not exist the DB:%s %s' %(self.system,opType))
      if params != None:
         dbSql = dbSql % params
      cur = None
      try:
         cur = self._dbconnection.cursor()
         self.__execute_sql(cur, selectStatement)
         row = cur.fetchone()
         return row
      finally :
         if cur :
            self._dbconnection.rollback() 
   
   def execute_op(self, opType, params=None):
      dbSql = self.getDBOperationInfo(opType)
      if dbSql=='':
         raise RuntimeError('ERROR:get db opreation info error,not exist the DB:%s %s' %(self.system,opType))
      if params != None:
         dbSql = dbSql % params
      self.execute_sql_string(dbSql)
      
   def opupdate(self,opType, params = None):
   #更新
      '''
      更新
      '''
      self.execute_op(opType, params)
   
   def opdelete(self,opType,params = None):
   #删除   
      '''
      删除
      '''
      self.execute_op(opType, params)
   
   def opinsert(self,opType,params = None):
   #插入
      '''
      插入
      '''      
      self.execute_op(opType, params)
      
   def check_op_in_db(self,opType,params=None):
      '''
      判断数据是否存在
      '''
      rows = self.opquery(opType, params)
      if not rows:
         raise AssertionError("Expected to have have at least one row from '%s:%s' "
                                 "but got 0 rows." % (self.getDBOperationInfo(opType), params))      
      
   def op_row_count(self,opType,params=None):
      '''
      查询结果记录数
      '''
      rows = self.opquery(opType, params)
      return 0 if rows==None else len(rows)
   
   def query_rowcount_should_be_equal(self,expect_rowsconut,opType,params=None):
      '''
      比较 预期记录数(expect_rowsconut) 与 查询结果记录数(result_rowscount)
      '''
      rows = self.opquery(opType, params)
      result_rowscount = 0 if rows==None else len(rows)
      if result_rowscount != int(expect_rowsconut):
         raise AssertionError("Expected same number of rows to be returned from '%s:%s' %s"
                                 "than the returned rows of %s" % (self.getDBOperationInfo(opType), params, expect_rowsconut, result_rowscount))
   
   def query_values_should_be_equal(self,expect_values,opType,params=None):
      '''
      比较 预期结果(expect_values) 与 查询结果(result_values) 是否一致

      expect_values 可以是单个值，也可以是list
      '''
      result_values = self.opquery_one(opType, params)
      if len(result_values) != len(expect_values):
         raise AssertionError('EXCEPTION:query_values_should_be_equal:%s:len(expect_values)[%s]!=len(result_values)[%s]' %(opType,expect_values,result_values))
         
      for i in range(0,len(result_values)):
         if result_values[i]!=expect_values[i]:
            raise AssertionError('EXCEPTION:query_values_should_be_equal:%s:expect_value[%s]!=result_value[%s]' %(opType,expect_values[i],result_values[i]))
            