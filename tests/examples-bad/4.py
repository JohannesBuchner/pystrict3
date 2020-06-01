def foo(a, b=1):
	return a*b
foo(1)  ## OK
foo(1, 2)  ## OK
foo(1, 2, 3)  ## error: wrong number of arguments
