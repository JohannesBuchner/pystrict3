class FooMany():
	def __init__(self, a):
		self.a = a
	def foo(self):
		print(self.a)
		self.b = 123
		print(self.c)  ## OK, assigned outside class

foo = FooMany("Hello!")
foo.c = 123


