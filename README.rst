pystrict3
----------

pystrict3 checks Python3 code for simple mistakes, such as

* calling functions with the wrong number of arguments,
* interpolating strings with the wrong number of arguments,
* shadowing and re-using variables

This complements other static analysers such as pyflakes, and
can be used alongside linters and code format checkers.

.. image:: https://travis-ci.org/JohannesBuchner/pystrict3.svg?branch=master
    :target: https://travis-ci.org/JohannesBuchner/pystrict3
.. image:: https://coveralls.io/repos/github/JohannesBuchner/pystrict3/badge.svg?branch=master
    :target: https://coveralls.io/github/JohannesBuchner/pystrict3?branch=master


Features
-------------

* Checks string interpolation '%' style for correct number of arguments
* Checks string interpolation str.format style for correct number of arguments
* Checks for access of undefined class attributes
* Checks for access of undefined class methods
* Checks for correct number of arguments to function, method and class init calls

Assumptions
-------------

pystrict3 assumes you are writing relatively dumb python code, so

* no monkey patching
* no magic attributes (__dict__, __local__) access that alters classes and variables
* no altering builtins, etc.


Rules
--------------

pystrict3 enforces that **variables are only assigned once**, and that python keywords are not overwritten. 
This avoids shadowing and change of semantics of variables, and leads to cleaner, more idiomatic code::

    parse = parse(foo)  ## bad
    node = get_node()
    node.foo()  ## ok, modification
    node += 3   ## ok, modification

    def format(...): ## bad, format is a keyword
    
    import requests, html
    
    html = requests.get(url)  ## bad: overwrites imported package name

pystrict3 checks that **functions are called with the
right number of arguments**. This catches bugs before execution, for example
when call signatures change to include an additional argument::

    def foo(a, b):
        return a*b
    foo(1, 2)  ## OK
    foo(123)  ## error: wrong number of arguments

    def bar(a, b=1):
        return a*b
    bar(1)  ## OK
    bar(1, 2)  ## OK
    bar(1, 2, 3)  ## error: wrong number of arguments


pystrict3 checks that **classes are instanciated with the right number of arguments**,
**methods are called with the right number of arguments**, and
**only attributes are accessed which have been assigned somewhere**.
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
    
    foo.foo(1) ## error, wrong number of arguments

pystrict3 **checks string interpolation** (printf-style % and str.format) 
for the correct number of arguments and keywords::

    print("Hello %s, it is %d:%02d" % ("World", 12, 34)) # OK
    print("Hello %s, it is %d:%02d" % ("World", 12)) # error
    '\n%s%*s' % (indent, len(key)+3, '')  # ok, variable length
    '{}{}'.format(1,2) # ok
    '{}{}'.format(1) # error
    '{}{}'.format(1,2,3) # error
    '{0}{1}{0}{2}'.format(1,2)  # error: missing index 2
    '{foo}{bar}'.format(foo=1, bar=2, baz=3)  # ok
    '{foo}{bar}'.format(foo=1, baz=3)  # error: missing bar



Contributing
--------------

Contributions are welcome.

pystrict3 is currently relatively dumb and may not catch all corner cases.
It tries hard to avoid unintentional false positives.

However, it is tested on activestate recipes, and 1131/1256 of all valid python3
programs already are pystrict3 compliant, indicating that its guidelines
are already adhered to. 

Usage
--------
Run with::

    $ python3 pystrict3.py <filenames>

Running with multiple filenames has the benefit that all
function signatures are first recorded and verified across all files.

Example stderr outputs::

    tests/expect-fail/recipe-412717.py:32: ERROR: Variable reuse: "Test"
    tests/expect-fail/recipe-425043.py:13: ERROR: Function "pow" (3..3 arguments) called with 2 arguments
    tests/expect-fail/recipe-578135.py:184: ERROR: Function "encode" (3..3 arguments) called with 2 arguments

Return code is 1 if a error was detected, or 0 otherwise.
For non-verbose, pipe stdout to /dev/null.

Future
--------

Programs where variables do not change are easier to optimize and parallelise.
Perhaps in the future, python compilers can take advantage of this.


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
        USE_JYTHON = True
    except:
        pass
    
    # new: re-arrange
    try:
        # ... code detecting something, which throws an exception
        USE_JYTHON = True
    except:
        USE_JYTHON = False
    # or use |= 
    USE_JYTHON |= True
    # or define a function
    USE_JYTHON = True
    
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

