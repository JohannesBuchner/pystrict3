class FooMany(object):
	def __init__(self, a):
		self.a = a
	def foo(self, b):
		self.fookwargs(self.a, self.b, c=1, d=2)
	def fookwargs(self, a, b, **kwargs):
		self.unknownmethod(a)



