
# some test functions:

def foo(a: float, b: int):
    pass


def foo2(a: float, b: int):
    if False:
        return a
    else:
        return b


def bar(a: int, b=3, c=False):
    return a + b


def baz(a, b):
    return a, b, a + b, 3

def indicator(r):
    if r > 42:
        return False
    else:
        return True

class Foo(object):
    def __init__(self, a: int, b=3):
        pass
    def calc(self):
        return 42
