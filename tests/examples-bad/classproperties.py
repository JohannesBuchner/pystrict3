class FooMany():
	def __init__(self, a):
		self.a = a
	def foo(self):
		print(self.a)
		print(self.b) ## error: self.b never assigned.

