#!/usr/bin/env python

""" Matrix-vector multiplication """
from functools import reduce

def matmult(m, v):
    nrows = len(m)
    w = [None] * nrows
    for row in range(nrows):
        w[row] = reduce(lambda x,y: x+y, list(map(lambda x,y: x*y, m[row], v)))
    return w
   

#................................................
if __name__=='__main__':
    m, n = 2, 3
    vec = list(range(1, n+1))
    mat = [[i*n+x+1 for x in range(n)] for i in range(m)]
    print('vec=', vec)
    print('mat=', mat)
    print('mat . vec=', matmult(mat, vec))
