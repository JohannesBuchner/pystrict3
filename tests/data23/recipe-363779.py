#!/usr/bin/python2.4

"""Demonstrate function decorators."""

import sys
import time


def logged(when):

    """Log every invocation of the function.

    when -- This should be "pre" or "post".  If "post", then I'll also time
        the function, which may be useful for profiling.

    """

    def log(f, *args, **kargs):
        print("""\
Called:
  function: %s
  args: %s
  kargs: %s""" % (repr(f), repr(args), repr(kargs)), file=sys.stderr)

    def pre_logged(f):
        def wrapper(*args, **kargs):
            log(f, *args, **kargs)
            return f(*args, **kargs)
        return wrapper

    def post_logged(f):
        def wrapper(*args, **kargs):
            start = time.time()
            try:
                return f(*args, **kargs)
            finally:
                log(f, *args, **kargs)
                print("""\
  time delta: %s""" % (time.time() - start), file=sys.stderr)
        return wrapper

    try:
        return {"pre": pre_logged, "post": post_logged}[when]
    except KeyError as e:
        raise ValueError(e)


@logged("post")
def hello(name):
    print("Hello,", name)


hello("World!")
