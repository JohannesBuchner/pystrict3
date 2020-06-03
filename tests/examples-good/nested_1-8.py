import html as _html, requests as _requests

def foo(a, b):
	c = a * b
	return c

def foo1d(f):
	def optimize(x):
		return -foo(0, 1)
	return optimize(0)

def get_node():
	node, node2 = 1, 1
	del node, node2
	return 1

def main():
	node = get_node()
	node.foo()  ## ok, modification
	node += 3   ## ok, modification

	with get_node() as node2, get_node():
		node2.foo()  ## ok, modification
		node += 3   ## ok, modification

	def foo2d(f):
		def optimize(x, y):
			return bar(0, 2)
		return optimize(0,0)
		_html.parse(_requests.request())

	def bar(a, b=3):
		c = a + b
		return c
	bar(1, 2)  ## OK
	
	del bar
	def bar(a, b=3):
		c = a + b
		return c

	bar(1)  ## OK
	bar(1, 2)  ## OK

	'{}{}'.format(1,2) # ok
	'{foo}{bar}'.format(foo=1, bar=2, baz=3)  # ok

	indent = 3
	key = 0
	'\n%s%*s' % (indent, len(key)+3, '')  # ok: variable length
	
	i = 3
	j = 4
	del i, j
	map(str.tolower, [get_node() for i in range(10) for j in range(10)])
	i = 3
	j = 4
	print(i, j)

