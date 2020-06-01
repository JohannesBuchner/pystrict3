def foo1d(f):
	def optimize(x):
		return -f(x)
	return optimize(0)

def foo2d(f):
	def optimize(x, y):
		return f(x, y)
	return optimize(0,0)

foo1d(lambda x: x)
foo2d(lambda x, y: x)
