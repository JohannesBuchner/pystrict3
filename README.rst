pystrict3
----------

pystrict3 is a fast plausibility code analyser for Python3.

Thanks to static code analysis, it checks Python3 code for obvious mistakes,
such as

* calling functions with the different number of arguments than they are defined with.
* accessing attributes and methods that are never set.
* documenting the wrong number of arguments.
* using variables that are never set.

Without running your python code!

This tool complements other static analysers such as pyflakes, and
can be used alongside linters and code format checkers (such as pylint and flake8).

.. image:: https://github.com/JohannesBuchner/pystrict3/actions/workflows/tests.yml/badge.svg
    :target: https://github.com/JohannesBuchner/pystrict3/actions/workflows/tests.yml
.. image:: https://coveralls.io/repos/github/JohannesBuchner/pystrict3/badge.svg?branch=master
    :target: https://coveralls.io/github/JohannesBuchner/pystrict3?branch=master

pystrict3 assumes that no monkey patching of builtin behaviour or
magic attributes (__dict__, __local__) alter classes and variables behind the scenes.
Python 3.5 and above is required.

Function calls
----------------

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

pystrict3 also checks docstrings for documented arguments and returns
(numpydoc, rst and google-style is supported).
It does not give an error if no docstrings are present. 
However, if only part of the arguments are documented, it gives an 
error pointing out the missing arguments to document.

For example::

    def compute(num1, num2):
        """
        Combined two integer numbers.

        Parameters
        ----------
        num1 : int
            First number to add.
        
        Returns
        -------
        sum: int
            first number plus second number
        int
            first number minus second number
        """:
            return num1 + num2, num1 - num2, num1

This would raise two warnings:

1. parameter num2 is not documented
2. a triple is returned, but a tuple is documented.

Redefined variable
-------------------

pystrict3 (--allow-redefining disables this behaviour) can enforce that 
variables are only assigned once. 
This avoids changing the meaning of variables, and leads to cleaner, more idiomatic code
with fewer side-effects.

It also prevents overwriting python builtins. Some examples::

    parse = parse(foo)    ## bad
    node = get_node()
    node.foo()            ## ok, modification
    node += 3             ## ok, modification

    def format(...):      ## bad, format is a python keyword
    
    import requests, html
    
    html = requests.get(url)  ## bad: overwrites imported package name



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


Synapsis
--------
::

    $ pystrict3.py --help

    usage: pystrict3.py [-h] [--import-builtin] [--import-any] [--allow-redefining] [--verbose] filenames [filenames ...]

    pystrict3: a Python code checker. Checks number of arguments in function, class init and method calls. Optionally also checks calls to imported modules. Checks that class attributes accessed are assigned somewhere. Checks that builtin names are
    not overwritten. Checks that variables are only assigned once.

    positional arguments:
      filenames           python files to parse

    options:
      -h, --help          show this help message and exit
      --import-builtin    Also load builtin python modules to check function signatures. (default: False)
      --import-any        Also load any modules specified in import statements to check function signatures. Warning: can execute arbitrary module code. (default: False)
      --allow-redefining  Allow redefining variables. (default: False)
      --verbose, -v       More verbose logging output. (default: False)

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
    Summary:
      - checked 287 function calls. 
      - checked definition of 469 new and access of 393 variables.
      - checked 4 docstrings.
    pystrict3: OK

Return code is non-zero if a error was detected, or 0 otherwise.

For verbose output, pipe stdout to /dev/null.

Licence
---------

BSD 2-clause.


Tipps
------

It's OK to have some pystrict3 warnings and errors. Take them as guidance towards
cleaner code.


How to write code that does not shadow or override variables:

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
