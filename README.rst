pystrict3
----------

pystrict3 statically checks Python3 code for simple mistakes, such as

* calling functions with the wrong number of arguments
* accessing attributes and methods that are never defined
* shadowing and re-using variables

This complements other static analysers such as pyflakes, and
can be used alongside linters and code format checkers (such as pylint and flake8).

.. image:: https://travis-ci.org/JohannesBuchner/pystrict3.svg?branch=master
    :target: https://travis-ci.org/JohannesBuchner/pystrict3
.. image:: https://coveralls.io/repos/github/JohannesBuchner/pystrict3/badge.svg?branch=master
    :target: https://coveralls.io/github/JohannesBuchner/pystrict3?branch=master


Assumptions
-------------

pystrict3 assumes unsurprising Python code, so

* no monkey patching
* no magic attributes (__dict__, __local__) that alter classes and variables
* no altering builtins, etc.

Python 3.5 and above is required.

Rules
--------------

pystrict3 enforces that variables are only assigned once. 
This avoids shadowing and change of semantics of variables, and leads to cleaner, more idiomatic code
with fewer side-effects. It also prevents overwriting python builtins.::

    parse = parse(foo)    ## bad
    node = get_node()
    node.foo()            ## ok, modification
    node += 3             ## ok, modification

    def format(...):      ## bad, format is a python keyword
    
    import requests, html
    
    html = requests.get(url)  ## bad: overwrites imported package name

pystrict3 checks that functions are called with the
right number of arguments. This catches bugs before execution, for example
when call signatures change to include an additional argument::

    def foo(a, b):
        return a*b
    foo(1, 2)        ## OK
    foo(123)         ## error: wrong number of arguments

    def bar(a, b=1):
        return a*b
    bar(1)           ## OK
    bar(1, 2)        ## OK
    bar(1, 2, 3)     ## error: wrong number of arguments
    
    # builtin module signatures are verified too:
    import os, numpy
    os.mkdir("foo", "bar") ## error: wrong number of arguments (if run with --load-builtin-modules)
    numpy.exp()            ## error: wrong number of arguments (if run with --load-any-modules)


pystrict3 checks that classes are instanciated with the right number of arguments,
methods are called with the right number of arguments, and
only attributes are accessed which have been assigned somewhere.
This catches bugs before execution, for example
when call signatures change to include an additional argument::

    class Foo():
        def __init__(self, a):
            self.a = a
        def foo(self):
            self.b = 3
            print(self.a) ## OK
        def bar(self, c):
            print(self.b) ## OK
            return self.c ## error, because never assigned
    
    Foo(1, 2)  ## error: wrong number of arguments for __init__
    foo = Foo(1)  ## OK

    # real example:
    class Ellipse:
        def __init__(self,center,radius_x,radius_y,fill_color,line_color,line_width):
            self.center = center
            self.radiusx = radius_x
            self.radiusy = radius_y
            self.fill_color = fill_color
            self.line_color = line_color
            self.line_width = line_width
        def strarray(self):
            return ["  <ellipse cx=\"%d\" cy=\"%d\" rx=\"%d\" ry=\"%d\"\n" %\
                (self.center[0],self.center[1],self.radius_x,self.radius_y),
                "    style=\"fill:%s;stroke:%s;stroke-width:%d\"/>\n" % (colorstr(self.fill_color),colorstr(self.line_color),self.line_width)]
            # error above: self.radius_x vs self.radiusx


Contributing
--------------

Contributions are welcome.

pystrict3 may not catch all corner cases.
It tries hard to avoid unintentional false positives, and has a very
high code coverage with integration tests (see runtests.sh and tests/ directory).

Tested on activestate recipes, approximately half of all valid python3
programs are pystrict3 compliant, indicating that its guidelines
are already adhered to.

Install
-------
::

    $ pip3 install pystrict3

Usage
--------
Run with::

    $ python3 pystrict3.py <filenames>
    $ python3 pystrict3.py --import-builtin <filenames>
    $ python3 pystrict3.py --import-any <filenames>

Running with multiple filenames has the benefit that all
function signatures are first recorded and verified across all files.

Running with `--import-builtin` checks function calls to builtin
modules.

Running with `--import-any` checks function calls to any modules,
but this requires pystrict3 to import them, potentially running arbitrary
module code.


Example stderr outputs::

    tests/expect-fail/recipe-412717.py:32: ERROR: Variable reuse: "Test"
    tests/expect-fail/recipe-425043.py:13: ERROR: Function "pow" (3..3 arguments) called with 2 arguments
    tests/expect-fail/recipe-578135.py:184: ERROR: Function "encode" (3..3 arguments) called with 2 arguments

Return code is 1 if a error was detected, or 0 otherwise.
For non-verbose, pipe stdout to /dev/null.

Licence
---------

BSD 2-clause.


Tipps
------

It's OK to not be pystrict3 compliant. It can serve as guidance towards
cleaner code.


How to write to pystrict3 compliance:

* Use del to actively remove unused variables::
     
     answer = input("Do you want to play? (yes/no)")
     if answer == "no":
         sys.exit()
     del answer
     answer = int(input("first value"))
     print(answer * 10):

* Name parts of computation explicitly::
 
     # bad:
     magicnumber = sys.argv[1]
     magicnumber = int(magicnumber)
     # better:
     magicnumberstr = sys.argv[1]
     magicnumber = int(magicnumberstr)
     
     
     filename = 'foo.pdf'
     if condition:
        filename = 'foo.png'  # bad
     
     # better:
     if condition:
        filename = 'foo.png'
     else:
        filename = 'foo.pdf'
     
     # bad:
     path = os.path.basename(sys.argv[1])
     path = path + filename   # bad: variable changes meaning
     path = path + extension

     # better:
     components = []
     components.append(os.path.basename(sys.argv[1]))
     components.append(filename)
     components.append(extension)
     path = ''.join(components)

* Refactor into functions::

    # original: "changes" is being reused.
    USE_JYTHON = False
    try:
        # ... code detecting something, which throws an exception
        USE_JYTHON = True  ## re-assigning: not allowed
        # could use instead:
        # USE_JYTHON |= True
    except:
        pass
    # or define a function
    USE_JYTHON = check_jython()
    
    # original: a sorting construct
    changes = True
    while changes:
        changes = False
        for a in ...:
            if ...:
                changes = True
                break
        if not changes:
            break
    
    # new: function returns when no further changes are needed
    def mysort(objs):
        while True:
            changes = False
            for a in ...:
                if ...:
                    changes = True
                    break
            if not changes:
                return objs

* Instead of assigning to __doc__, move the docstring to the start of the file.

