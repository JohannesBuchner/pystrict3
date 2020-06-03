class Hello():
	def __init__(self):
		self.name = 'World'

print('{2}{1}{0.name}'.format(Hello(), 2, 1))
print('{number}{obj.name}'.format(obj=Hello(), number=2))
args = [Hello(), 2, 1]
kwargs = dict(obj=Hello(), number=2)
print('{3}{2}{1.name}'.format(*args))
print('{number}{obj.name}'.format(**kwargs))
