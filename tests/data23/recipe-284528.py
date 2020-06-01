"""Implements a nice syntax for cooperative methods.
Could be made working for staticmethods and classmethods,
but who needs them anyway? ;)"""

import inspect

def second_arg(func):
    args = inspect.getargspec(func)[0]
    if len(args) >= 2: return args[1]

class _Cooperative(type):
    def __init__(cls, name, bases, dic):
        for n,func in dic.items():
            setattr(cls, n, func)
    def __setattr__(cls, name, func):
        set = super(_Cooperative, cls).__setattr__
        if inspect.isfunction(func) and second_arg(func) == "super":
            set(name, lambda self, *args, **kw : 
                func(self, super(cls, self), *args, **kw))
        else:
            set(name, func)

class Cooperative(metaclass=_Cooperative):
    pass


if __name__ == "__main__":
    class B(Cooperative):
        def print_(self):
            print("B", end=' ')
    class C(B):
        def print_(self, super):
            super.print_()
            print("C", end=' ')
    class D(C):
        def print_(self, super):
            super.print_()
            print("D", end=' ')
    D().print_() # => B C D
