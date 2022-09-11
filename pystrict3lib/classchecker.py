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

import logging
import ast
import sys
from .funcchecker import FuncLister, count_call_arguments

internal_members = set(dir(object)).union(dir(classmethod)).union(dir(lambda x: x))


class MethodCallLister(ast.NodeVisitor):
    """Verifies all calls against call signatures in known_methods.

    Unknown functions are not verified.
    """

    def __init__(self, filename, class_name, known_methods, known_staticmethods):
        """
        :param filename: file name
        :param class_name: class name
        :param known_methods: list of methods
        :param known_staticmethods: list of static methods
        """
        self.filename = filename
        self.known_methods = known_methods
        self.known_staticmethods = known_staticmethods
        self.class_name = class_name
        self.log = logging.getLogger('pystrict3.classchecker')

    def visit_Call(self, node):
        self.generic_visit(node)
        if not (isinstance(node.func, ast.Attribute) and isinstance(node.func.value, ast.Name) and node.func.value.id == 'self'):
            return

        funcname = node.func.attr
        min_call_args, may_have_more = count_call_arguments(node)

        if funcname in self.known_staticmethods:
            min_args, max_args = self.known_staticmethods[funcname]
            is_staticmethod = True
        elif funcname in self.known_methods:
            min_args, max_args = self.known_methods[funcname]
            # self is supplied by Python
            min_call_args += 1
            is_staticmethod = False
        else:
            # this is already guaranteed by the ClassPropertiesLister
            return

        if max_args >= 0 and min_call_args > max_args:
            sys.stderr.write('%s:%d: ERROR: Class "%s": %s "%s" (%d..%d arguments) called with too many (%d%s) arguments\n' % (
                self.filename, node.lineno, self.class_name, 'static method' if is_staticmethod else 'method',
                funcname, min_args, max_args, min_call_args, '+' if may_have_more else ''))
            sys.exit(1)
        elif min_call_args < min_args and not may_have_more:
            sys.stderr.write('%s:%d: ERROR: Class "%s": %s "%s" (%d..%d arguments) called with too few (%d%s) arguments\n' % (
                self.filename, node.lineno, self.class_name, 'static method' if is_staticmethod else 'method',
                funcname, min_args, max_args, min_call_args, '+' if may_have_more else ''))
            sys.exit(1)
        else:
            self.log.debug("call(%s.%s with %d%s args): OK" % (self.class_name, funcname, min_call_args, '+' if may_have_more else ''))


class ClassPropertiesLister(ast.NodeVisitor):
    """Verifies accessed properties are set at some point in the same class."""

    def __init__(self, filename):
        """
        :param filename: file name
        """
        self.filename = filename
        self.log = logging.getLogger('pystrict3.classchecker')

    def visit_ClassDef(self, node):
        self.generic_visit(node)
        # skip subclasses metaclasses and other fancy things
        derived_class = len(node.bases) > 1 \
            or len(node.bases) > 0 and not (len(node.bases) == 1 and isinstance(node.bases[0], ast.Name) and node.bases[0].id == 'object') \
            or len(node.keywords) > 0 or len(node.decorator_list) > 0
        # standalone class

        # collect all members
        known_attributes = set()
        known_members = set(internal_members)
        for child in ast.iter_child_nodes(node):
            if isinstance(child, ast.FunctionDef):
                self.log.debug("+%s.%s()" % (node.name, child.name))
                known_members.add(child.name)
            if isinstance(child, ast.Assign):
                for target in child.targets:
                    for name in ast.walk(target):
                        if isinstance(name, ast.Name):
                            self.log.debug("+%s.%s" % (node.name, name.id))
                            known_attributes.add(name.id)
            del child

        # collect all assigns
        for child in ast.walk(node):
            if isinstance(child, ast.Attribute) and isinstance(child.value, ast.Name) and child.value.id == 'self' and isinstance(child.ctx, ast.Store):
                known_attributes.add(child.attr)
            del child

        for child in ast.walk(node):
            if isinstance(child, ast.Attribute) and isinstance(child.value, ast.Name) and child.value.id == 'self' and isinstance(child.ctx, ast.Load):
                if child.attr in known_attributes:
                    self.log.debug("accessing attribute %s.%s: OK" % (node.name, child.attr))
                    continue
                if child.attr in known_members:
                    self.log.debug("accessing member %s.%s: OK" % (node.name, child.attr))
                    continue

                if derived_class:
                    self.log.debug("accessing unknown member %s.%s: possibly OK, derived class" % (node.name, child.attr))
                    continue

                sys.stderr.write('%s:%d: ERROR: accessing unknown class attribute "%s.%s"\n' % (
                    self.filename, child.lineno, node.name, child.attr))
                sys.exit(1)

        # verify class members
        funcs = FuncLister(filename=self.filename)
        funcs.visit(node)

        MethodCallLister(
            filename=self.filename, class_name=node.name,
            known_methods=funcs.known_functions, known_staticmethods=funcs.known_staticmethods
        ).visit(node)
