# -*- coding: utf-8 -*-


from dblib import DatabaseLibrary

def test_query():
   db = DatabaseLibrary()
   db.connect_to_database('cx_Oracle', 'mpay', 'nac_user', 'dqa_testic', '172.20.5.165', '1521')
   sql = 'select *  from t_l_terminal where LT_TERMNO=80014099'
   rows = db.query(sql)
   for row in rows:
      print row
   db.disconnect_from_database()

def test_query2():
   #|  | execute sql string  | update t_l_terminal set status='${status}' where lt_termno='${lt_termno}' and lt_merchno='${lt_merchno}'
   db = DatabaseLibrary()
   db.connect_to_database('cx_Oracle', 'mpay', 'nac_user', 'dqa_testic', '172.20.5.165', '1521')
   sql = "select *  from t_l_terminal where lt_termno='80014099'"
   rows = db.query(sql)
   for row in rows:
      print row
   db.disconnect_from_database()

def test_exec():
   #|  | execute sql string  | update t_l_terminal set status='${status}' where lt_termno='${lt_termno}' and lt_merchno='${lt_merchno}'
   db = DatabaseLibrary()
   db.connect_to_database('cx_Oracle', 'mpay', 'nac_user', 'dqa_testic', '172.20.5.165', '1521')
   sql = "update t_l_terminal set lt_stauts='1' where lt_termno='80014099'"
   ret = db.execute_sql_string(sql)
   db.disconnect_from_database()

if __name__ == '__main__':
   test_exec()
   
   