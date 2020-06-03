def foo(x):
	return x

def bar():
	return 1

def baz(x, y):
	return x

foo(1)
args = [1]
foo(*args)
bar(*[])
args.append(2)
baz(*args)

kwargs = dict(x=2)
foo(**kwargs)
kwargs['y'] = 3
baz(**kwargs)

