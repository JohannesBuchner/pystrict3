indent = 3
key = "foo"
print('\n%s%*s' % (indent, len(key)+3, 'Hello'))  # ok: variable length

print("%.*f" % (indent, 1.2345))
def myprint(x, *args):
	print("%.3f %.4f %10.3f %1.*f" % (x, x, x, 3, x))

myprint(3)

