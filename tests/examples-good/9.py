"""foo bar"""

del __doc__
__doc__ = """foo baz"""

map(str.lower, dir(__builtins__)) ## ok, builtin names

