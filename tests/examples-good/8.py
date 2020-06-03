indent = 3
key = 0
'\n%s%*s' % (indent, len(key)+3, '')  # ok: variable length

tmp = "%.*f" % (key, indent)
def myprint(x, *args):
	print("%.3f %.4f %10.3f %1.*f" % (x, x, x, key, 3))

myprint(3)

