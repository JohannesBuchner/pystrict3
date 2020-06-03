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
import keyword
import builtins
#import pprintast
#from classchecker import 
from .funcchecker import FuncLister, CallLister
from .stringchecker import StrFormatLister
from .classchecker import ClassPropertiesLister

preknown = set(builtins.__dict__).union({'__doc__', '__file__', '__name__', '__annotations__', '__dict__', '__builtins__'})

def flat_walk(node):
    #print(node)
    yield node
    if not isinstance(node, ast.FunctionDef) and not isinstance(node, ast.ClassDef) and not isinstance(node, ast.Lambda) and not isinstance(node, ast.Import) and not isinstance(node, ast.ImportFrom):
        for child in ast.iter_child_nodes(node):
            #print(node, child)
            yield from flat_walk(child)

def function_walk(node):
    if isinstance(node, ast.FunctionDef) or isinstance(node, ast.ClassDef) or isinstance(node, ast.Lambda):
        yield node
    for child in ast.iter_child_nodes(node):
        yield from function_walk(child)

def get_ids(node):
    if hasattr(node, 'id'):
        yield node.id
    if hasattr(node, 'target'):
        yield from get_ids(node.target)
    if hasattr(node, 'elts'):
        for el in node.elts:
            yield from get_ids(el)
    #if node is not None:
    #    print("ids from:")
    #    pprintast.pprintast(node)


def assert_unknown(name, known, node, filename):
    assert name is not None
    if name in known:
        sys.stderr.write('%s:%d: ERROR: Variable reuse: "%s"\n' % (filename, node.lineno, name))
        sys.exit(1)

def check_new_identifiers(known, node, filename):
    add_here = set()
    forget_here = set()
    for el in flat_walk(node):
        #print(el, list(get_ids(getattr(el, 'target', None))), [n.asname or n.name for n in getattr(el, 'names', [])], [list(get_ids(t)) for t in getattr(el, 'targets', [])], [list(get_ids(t)) for t in getattr(el, 'generators', [])])
        # find all name nodes and look at ids
        if hasattr(el, 'names'):
            names = el.names
            for name in names:
                if getattr(name, 'asname', None) is not None:
                    name = getattr(name, 'asname')
                elif hasattr(name, 'name'):
                    name = name.name
                #print("+%s" % name)
                assert_unknown(name, known, node, filename)
                name = name.split('.')[0]
                add_here.add(name)
            del name, names
        if hasattr(el, 'targets'):
            targets = el.targets
            for target in targets:
                for id in get_ids(target):
                    if isinstance(getattr(target, 'ctx'), ast.Del):
                        print("-%s" % id)
                        if id in add_here:
                            add_here.remove(id)
                        if id in known:
                            known.remove(id)
                    else:
                        #print("+%s" % id)
                        assert_unknown(id, known, node, filename)
                        add_here.add(id)
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
                    add_here.add(id)
                del names
            del item, items
        if hasattr(el, 'target'):
            for id in get_ids(el.target):
                add_here.add(id)
        if hasattr(el, 'generators'):
            generators = el.generators
            for target in generators:
                for id in get_ids(target):
                    #print("+%s" % id)
                    assert_unknown(id, known, node, filename)
                    add_here.add(id)
                    forget_here.add(id)
            del target, generators
        if hasattr(el, 'name'):
            if el.name is not None:
                assert_unknown(el.name, known, node, filename)
                add_here.add(el.name)
        if not isinstance(getattr(el, 'ctx', None), ast.Del):
            for id in get_ids(el):
                #print("   using: %s" % id)
                if keyword.iskeyword(id):
                    pass
                elif id in known or id in add_here:
                    pass
                else:
                    sys.stderr.write('%s:%d: ERROR: Variable unknown: "%s"\n' % (filename, node.lineno, id))
                    sys.exit(1)
        
        for id in forget_here:
            if id in known:
                print('-%s' % id)
                known.remove(id)

    for id in add_here:
        if id not in known:
            print('+%s' % id)
            known.add(id)
    for id in forget_here:
        if id in known:
            print('-%s' % id)
            known.remove(id)


def main(filenames):
    known_functions = dict()

    asts = []
    for filename in filenames:
        a = ast.parse(open(filename).read())

        StrFormatLister(filename=filename).visit(a)
        ClassPropertiesLister(filename=filename).visit(a)
        
        funcs = FuncLister(filename=filename)
        funcs.visit(a)
        known_functions.update(funcs.known_functions)
        
        
        asts.append((filename, a))

    for filename, a in asts:
        known = set(preknown)

        CallLister(filename=filename, known_functions=known_functions).visit(a)
        
        for node in a.body:
            #print()
            #print(node)
            #pprintast.pprintast(node)
            #print(known - set(builtins.__dict__))
            #print(''.join(open(sys.argv[1]).readlines()[node.lineno-3:node.lineno+2]))
            check_new_identifiers(known, node, filename)
            del node

        parents = [a.body] + [c.body for c in a.body if isinstance(c, ast.ClassDef)]
        functions = []
        for p in parents:
            for func in p:
                if not isinstance(func, ast.FunctionDef):
                    continue
                
                # add func argument names to known
                known_with_args = set(known)
                arguments = func.args
                known_with_args = known_with_args.union({arg.arg for arg in arguments.args})
                known_with_args = known_with_args.union({arg.arg for arg in arguments.kwonlyargs})
                if arguments.vararg is not None:
                    known_with_args.add(arguments.vararg.arg)
                if arguments.kwarg is not None:
                    known_with_args.add(arguments.kwarg.arg)
                
                for node in func.body:
                    check_new_identifiers(known_with_args, node, filename)
        
    #print(known - preknown)


