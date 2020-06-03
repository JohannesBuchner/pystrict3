class FooMany():
	def __init__(self, a = None):
		self.c, (self.cc, self.ccc) = 1, (2, "foo")
		if a is not None:
			self.a = a
		self.d = self.e = 0
	def foo(self):
		print(self.a)  ## OK, assigned in init
		print(self.b)  ## OK, assigned in bar
		print(self.c, self.cc, self.ccc)  ## OK, assigned in init
		print(self.d, self.e)  ## OK, assigned in init
	def bar(self):
		self.b = 123

foo = FooMany("Hello!")


