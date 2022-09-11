def foo(x):
    return x
del x  ## error, x should not leak out of foo
