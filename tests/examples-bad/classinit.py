class FooMany():
	def __init__(self, *args):
		pass

FooMany(foo=3)

class FooMany2():
	def __init__(self, **kwargs):
		pass

foo = FooMany2(1, 2, 3)

class Foo0():
	def __init__(self):
		pass

Foo0()
Foo0(123)  ## error expected: takes zero arguments

