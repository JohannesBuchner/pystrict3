#!/usr/bin/env python3
"""
BSD 2-Clause License

Copyright (c) 2020, Johannes Buchner
All rights reserved.

Redistribution and use in source and binary forms, with or without
modification, are permitted provided that the following conditions are met:

1. Redistributions of source code must retain the above copyright notice, this
   list of conditions and the following disclaimer.

2. Redistributions in binary form must reproduce the above copyright notice,
   this list of conditions and the following disclaimer in the documentation
   and/or other materials provided with the distribution.

THIS SOFTWARE IS PROVIDED BY THE COPYRIGHT HOLDERS AND CONTRIBUTORS "AS IS"
AND ANY EXPRESS OR IMPLIED WARRANTIES, INCLUDING, BUT NOT LIMITED TO, THE
IMPLIED WARRANTIES OF MERCHANTABILITY AND FITNESS FOR A PARTICULAR PURPOSE ARE
DISCLAIMED. IN NO EVENT SHALL THE COPYRIGHT HOLDER OR CONTRIBUTORS BE LIABLE
FOR ANY DIRECT, INDIRECT, INCIDENTAL, SPECIAL, EXEMPLARY, OR CONSEQUENTIAL
DAMAGES (INCLUDING, BUT NOT LIMITED TO, PROCUREMENT OF SUBSTITUTE GOODS OR
SERVICES; LOSS OF USE, DATA, OR PROFITS; OR BUSINESS INTERRUPTION) HOWEVER
CAUSED AND ON ANY THEORY OF LIABILITY, WHETHER IN CONTRACT, STRICT LIABILITY,
OR TORT (INCLUDING NEGLIGENCE OR OTHERWISE) ARISING IN ANY WAY OUT OF THE USE
OF THIS SOFTWARE, EVEN IF ADVISED OF THE POSSIBILITY OF SUCH DAMAGE.

"""

import ast
import sys
import builtins
from .funcchecker import FuncLister, CallLister, ModuleCallLister
from .classchecker import ClassPropertiesLister

preknown = set(builtins.__dict__).union({'__doc__', '__file__', '__name__', '__annotations__', '__dict__', '__builtins__'})


def flat_walk(node):
    """ get all code components that are not functions, classes """
    yield node
    if not isinstance(node, ast.FunctionDef) and not isinstance(node, ast.ClassDef) and not isinstance(node, ast.Lambda) \
            and not isinstance(node, ast.Import) and not isinstance(node, ast.ImportFrom):

        for child in ast.iter_child_nodes(node):
            yield from flat_walk(child)


def get_ids(node):
    """get all ids defined in names, tuples and targets here"""
    if hasattr(node, 'id'):
        yield node.id
    if hasattr(node, 'target'):
        yield from get_ids(node.target)
    if hasattr(node, 'elts'):
        for el in node.elts:
            yield from get_ids(el)


def assert_unknown(name, known, node, filename):
    """unified error message verifying `name` is in set `known`"""
    assert name is not None
    # the nested if allows deleting builtins and re-defining them afterwards
    if name in known:
        if name in preknown:
            sys.stderr.write('%s:%d: ERROR: Overwriting builtin variable: "%s"\n' % (filename, node.lineno, name))
            sys.exit(1)
        elif name != '_':  # throwaway variable is allowed
            sys.stderr.write('%s:%d: ERROR: Variable reuse: "%s", previously defined in line %d\n' % (filename, node.lineno, name, known[name]))
            sys.exit(1)

def block_terminates(statements):
    for statement in statements:
        if isinstance(statement, ast.Return):
            return True
        if isinstance(statement, ast.Expr) and isinstance(statement.value, ast.Call) and isinstance(statement.value.func, ast.Attribute) and isinstance(statement.value.func.value, ast.Name):
            if statement.value.func.value.id == 'sys' and statement.value.func.attr == 'exit':
                return True
    return False

def check_new_identifiers(known, node, filename):
    """add newly defined variables and verify that the accessed ones are defined in known"""
    add = {}
    forget = set()
    for el in flat_walk(node):
        add_here = {}
        forget_here = set()
        # find all name nodes and look at ids
        if hasattr(el, 'names'):
            names = el.names
            for name in names:
                if getattr(name, 'asname', None) is not None:
                    name = getattr(name, 'asname')
                elif hasattr(name, 'name'):
                    name = name.name
                assert_unknown(name, known, node, filename)
                name = name.split('.')[0]
                add_here[name] = el.lineno
            del name, names
        if hasattr(el, 'targets'):
            targets = el.targets
            for target in targets:
                for id in get_ids(target):
                    if isinstance(getattr(target, 'ctx'), ast.Del):
                        print("-%s" % id)
                        if id in add:
                            del add[id]
                        if id in add_here:
                            del add_here[id]
                        if id in known:
                            del known[id]
                    else:
                        assert_unknown(id, known, node, filename)
                        add_here[id] = el.lineno
            del target, targets
        if hasattr(el, 'items'):
            items = el.items
            for item in items:
                if item.optional_vars is None:
                    names = item.context_expr
                else:
                    names = item.optional_vars
                for id in get_ids(names):
                    assert_unknown(id, known, node, filename)
                    add_here[id] = el.lineno
                del names
            del item, items
        if hasattr(el, 'target'):
            for id in get_ids(el.target):
                add_here[id] = node.lineno
        if hasattr(el, 'generators'):
            generators = el.generators
            for target in generators:
                for id in get_ids(target):
                    assert_unknown(id, known, node, filename)
                    add_here[id] = el.lineno
                    forget_here.add(id)
            del target, generators
        if hasattr(el, 'name'):
            if el.name is not None:
                assert_unknown(el.name, known, node, filename)
                add_here[el.name] = el.lineno
        if not isinstance(getattr(el, 'ctx', None), ast.Del):
            for id in get_ids(el):
                if id in known or id in add or id in add_here:
                    pass
                elif isinstance(node, ast.Try) and any(isinstance(handler.type, ast.Name) and handler.type.id == 'NameError' for handler in node.handlers if isinstance(handler, ast.ExceptHandler)):
                    # this is in a construct for testing whether a variable exists
                    pass
                else:
                    sys.stderr.write('%s:%d: ERROR: Variable unknown: "%s"\n' % (filename, el.lineno, id))
                    sys.exit(1)

        terminating_here = hasattr(el, 'body') and block_terminates(el.body)
        if not terminating_here:
            add.update(add_here)
            forget |= forget_here
        del forget_here, add_here
    
    for id, lineno in add.items():
        if id not in known:
            print('+%s' % id)
            known[id] = lineno
    for id in forget:
        if id in known:
            print('-%s' % id)
            del known[id]


def main(filenames, module_load_policy='none'):
    """ Verify python files listed in filenames """
    known_functions = dict()
    FuncLister.load_builtin_functions()

    asts = []
    for filename in filenames:
        a = ast.parse(open(filename).read())

        print("%s: checking class usage ..." % filename)
        ClassPropertiesLister(filename=filename).visit(a)
        print("%s: checking internals usage ..." % filename)
        ModuleCallLister(filename=filename, load_policy=module_load_policy).visit(a)
        
        funcs = FuncLister(filename=filename)
        funcs.visit(a)
        known_functions.update(funcs.known_functions)
        
        asts.append((filename, a))

    for filename, a in asts:
        known = {k: 'builtin' for k in preknown}

        print("%s: checking calls ..." % filename)
        CallLister(filename=filename, known_functions=known_functions).visit(a)
        
        print("%s: checking variables ..." % filename)
        for node in a.body:
            check_new_identifiers(known, node, filename)
            del node

        parents = [a.body] + [c.body for c in a.body if isinstance(c, ast.ClassDef)]
        for p in parents:
            for func in p:
                if not isinstance(func, ast.FunctionDef):
                    continue
                
                # add func argument names to known
                known_with_args = dict(**known)
                arguments = func.args
                known_with_args.update({arg.arg:func.lineno for arg in arguments.args})
                known_with_args.update({arg.arg:func.lineno for arg in arguments.kwonlyargs})
                if arguments.vararg is not None:
                    known_with_args[arguments.vararg.arg] = func.lineno
                if arguments.kwarg is not None:
                    known_with_args[arguments.kwarg.arg] = func.lineno
                
                for node in func.body:
                    check_new_identifiers(known_with_args, node, filename)

    print("pystrict3: OK")
