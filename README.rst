pystrict3
----------

pystrict3 is a static code analyser.

Rules
--------------

pystrict3 enforces that variables are only assigned once, and that python keywords are not overwritten. 
This avoids shadowing and change of semantics of variables, and leads to cleaner, more idiomatic code::

    parse = parse(foo)  ## bad
    node = get_node()
    node.foo()  ## ok, modification
    node += 3   ## ok, modification

    def format(...): ## bad, format is a keyword
    
    import requests, html
    
    html = requests.get(url)  ## bad: overwrites imported package name

pystrict3 checks that functions are called with the
right number of arguments. This catches bugs before execution, for example
when call signatures change to include an additional argument::

    def foo(a, b):
        return a*b
    foo(1, 2)  ## OK
    foo(123)  ## error: wrong number of arguments

    def bar(a, b=1):
        return a*b
    foo(1)  ## OK
    foo(1, 2)  ## OK
    foo(1, 2, 3)  ## error: wrong number of arguments

pystrict3 checks that printf-style string interpolation is used with the 
right number of arguments::

    print("Hello %s, it is %d:%02d" % ("World", 12, 34)) # OK
    print("Hello %s, it is %d:%02d" % ("World", 12)) # error
    '\n%s%*s' % (indent, len(key)+3, '')  # error
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

    $ pystrict3 <filenames>

Running with multiple filenames has the benefit that all
function signatures are first recorded and verified across all files.

Future
--------

Programs where variables do not change are easier to optimize and parallelise.
Perhaps in the future, python compilers can take advantage of this.



Licence
---------

MIT and BSD 2-clause. Take your pick.


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
    
    # new: make a function for detection:
    try:
        # ... code detecting something, which throws an exception
        USE_JYTHON = True
    except:
        USE_JYTHON = False
    
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

