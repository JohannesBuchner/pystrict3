"""foo bar"""

del __doc__
__doc__ = """foo baz"""

map(str.tolower, __builtins__) ## ok, builtin names

