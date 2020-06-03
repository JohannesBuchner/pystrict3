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
from .funcchecker import FuncLister

def get_self_attrs(node):
    if isinstance(node, ast.Attribute) and isinstance(node.value, ast.Name) and node.value.id == 'self':
        yield node.value.a
    if hasattr(node, 'elts'):
        for el in node.elts:
            yield from get_self_attrs(el)


class MethodCallLister(ast.NodeVisitor):
    """Verifies all calls against call signatures in known_methods.
    Unknown functions are not verified."""
    def __init__(self, filename, known_methods):
        self.filename = filename
        self.known_methods = known_methods
    def visit_Call(self, node):
        self.generic_visit(node)
        if isinstance(node.func, ast.Attribute) and isinstance(node.func.value, ast.Name) and node.func.value.id == 'self':
            return
        
        #pprintast.pprintast(node)
        #print(type(node), type(node.func))
        funcname = node.func.id
        if funcname not in self.known_methods:
            return
        min_args, max_args = self.known_methods[funcname]
        nargs = 0
        for arg in node.args:
            if isinstance(arg, ast.Starred):
                # give up
                return
            nargs += 1
        for arg in node.keywords:
            nargs += 1
        
        # self is also supplied automatically by Python
        nargs += 1 
        
        if max_args >= 0 and nargs > max_args or nargs < min_args:
            sys.stderr.write('%s:%d: ERROR: Method "%s" (%d..%d arguments) called with %d arguments\n' % (
                self.filename, node.lineno, funcname, min_args, max_args, nargs))
            sys.exit(1)
        else:
            print("call(%s with %d args): OK" % (funcname, nargs))



class ClassPropertiesLister(ast.NodeVisitor):
    """Verifies that all class properties that are accessed inside a class
    are set at some point in the same class."""
    def __init__(self, filename):
        self.filename = filename
    def visit_ClassDef(self, node):
        self.generic_visit(node)
        # skip subclasses
        if len(node.bases) > 1:
            print("skipping checks on derived class %s" % node.name)
            return
        if not (len(node.bases) == 1 and isinstance(node.bases[0], ast.Name) and node.bases[0].id == 'object'):
            print("skipping checks on derived class %s" % node.name)
            return
        # standalone class
        
        # collect all members
        known_members = set()
        for child in ast.iter_child_nodes(node):
            if isinstance(child, ast.FunctionDef):
                known_members.add(child.name)
        
        # collect all assigns
        known_attributes = set()
        for child in ast.walk(node):
            if isinstance(child, ast.Attribute) and isinstance(child.value, ast.Name) and child.value.id == 'self' and isinstance(child.ctx, ast.Store):
                known_attributes.add(child.attr)
        
        for child in ast.walk(node):
            if isinstance(child, ast.Attribute) and isinstance(child.value, ast.Name) and child.value.id == 'self' and isinstance(child.ctx, ast.Load):
                if child.attr in known_attributes:
                    print("accessing attribute %s.%s: OK" % (node.name, child.attr))
                    continue
                if child.attr in known_members:
                    print("accessing member %s.%s: OK" % (node.name, child.attr))
                    continue
                sys.stderr.write('%s:%d: ERROR: accessing unknown class attribute "self.%s"\n' % (
                    self.filename, child.lineno, child.attr))
                sys.exit(1)
                
        
        # verify class members
        funcs = FuncLister(filename=self.filename)
        funcs.visit(node)
        
        known_methods = funcs.known_functions
        
        MethodCallLister(filename=self.filename, known_methods=known_methods).visit(node)

