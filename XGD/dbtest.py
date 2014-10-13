# -*- coding: utf-8 -*-


from dblib import DatabaseLibrary

def test_query():
   db = DatabaseLibrary()
   db.connect_to_database('cx_Oracle', 'mpay', 'nac_user', 'dqa_testic', '172.20.5.165', '1521')
   sql = 'select *  from t_l_terminal where LT_TERMNO=80014099'
   rows = db.query(sql)
   for row in rows:
      print row



if __name__ == '__main__':
   test_query()