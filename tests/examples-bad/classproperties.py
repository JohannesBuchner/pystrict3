class FooMany(object):
	def __init__(self, a):
		self.a = a
	def foo(self):
		print(self.a)
		self.b = 123
		print(self.unknown)  ## error: never assigned.

foo = FooMany("Hello")
foo.c = 123


