class Foo0():
	def __init__(self):
		pass

foo1 = Foo0()

class Foo0(): ## error: redefined class
	def __init__(self, a):
		pass

foo2 = Foo0()
