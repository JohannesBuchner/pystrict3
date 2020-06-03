class FooMany():
	FOO, BAR = 123, 345
	
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
		self.foo()
		print(self.FOO_FORMAT % self.FOO)
		self.permanent()
	
	FOO_FORMAT = "%d"
	
	@staticmethod
	def permanent():
		print("yes")

foo = FooMany("Hello!")

class FooBar(FooMany):
	def foo(self):
		print(self.unknown)  ## OK, not checking derived classes

class FooBaz(FooMany, FooBar):
	def foo(self):
		print(self.unknown)  ## OK, not checking complex classes

FooMany.permanent()
foo.permanent()

def makefancy(x):
	return x


class Bar():
	def __init__(self):
		self.fancyfoo(1, 2, 3) ## OK, not checking decorated functions
		self.varargsfunc(1, 2, 3, 4, 5) ## OK, provided enough args
		self.a = 3

	@makefancy
	def fancyfoo(self):
		print(self.a)  ## OK, not checking derived classes

	def varargsfunc(self, a, b, *args):
		pass
