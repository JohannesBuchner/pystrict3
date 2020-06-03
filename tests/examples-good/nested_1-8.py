def foo(a, b):
	c = a * b
	return c
def bar(a, b=3):
	c = a + b
	return c

def foo1d(f):
	def optimize(x):
		return -foo(0, 1)
	return optimize(0)

def foo2d(f):
	def optimize(x, y):
		return bar(0, 2)
	return optimize(0,0)

def get_node():
	return 1

def main():
	node = get_node()
	node.foo()  ## ok, modification
	node += 3   ## ok, modification

	bar(1)  ## OK
	bar(1, 2)  ## OK

	'{}{}'.format(1,2) # ok
	'{foo}{bar}'.format(foo=1, bar=2, baz=3)  # ok

	indent = 3
	key = 0
	'\n%s%*s' % (indent, len(key)+3, '')  # ok: variable length

