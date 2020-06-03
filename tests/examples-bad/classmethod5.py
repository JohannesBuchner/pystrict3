class FooMany(object):
	def __init__(self, a):
		self.a = a
	def foo(self, b):
		self.foovargs()
	def foovargs(self, a, b, *args):
		pass



