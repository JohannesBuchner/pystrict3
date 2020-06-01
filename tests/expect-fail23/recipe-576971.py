#!c:/python25/python.exe -u
# -*- coding: utf-8 -*-

import sys,os
import cgi
import cgitb; cgitb.enable()
#
print("""Content-Type: text/html;charset=UTF-8
""")
cgiform= cgi.FieldStorage()
if 'QUERY_STRING' in os.environ:
  query= cgi.urllib.unquote(os.environ['QUERY_STRING'])
else:
  query= """select * from dx order by code limit 10;"""


import MySQLdb, MySQLdb.cursors
mycon= MySQLdb.connect(host='localhost',port=3306, \
  db='airs', user='airs', passwd='airs', cursorclass=MySQLdb.cursors.DictCursor)
mycon.set_character_set('utf8')
mycur = mycon.cursor()
mycur.execute('SET NAMES utf8;')
# ===================================================
if len(sys.argv)>1:
  query= sys.argv[1]
mycur.execute(query);
print("[")
for x1 in mycur._rows:
  print("{", end=' ')
  nn= 0
  for x2 in x1:
    x3= x1[x2]
    if nn>0: print(",", end=' ')
    nn= 1
    if type(x3).__name__=='str':
      print("'%s':" % x2, "'%s'" % x3.replace("'","\\'"), end=' ')
    else:
      print("'%s':" % x2, x3, end=' ')
  print("},")
print("]")
