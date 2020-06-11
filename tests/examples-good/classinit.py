class FooMany():
	def __init__(self, *args):
		pass

FooMany()
FooMany(1, 2, 3)

class FooMany2():
	def __init__(self, **kwargs):
		pass

foo = FooMany2(foo=1, bar=2, baz=3)
bar = FooMany2()

class Foo0():
	def __init__(self):
		pass

Foo0()

class FooOne():
	def __init__(self, a):
		self.a = a
	def myfunc(self):
		print(self.a)


print(FooOne(123).a)
FooOne(123).myfunc()

