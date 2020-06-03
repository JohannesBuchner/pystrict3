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


def count_function_min_arguments(arguments):
    """ returns minimum number of arguments. """
    return len(arguments.args) - len(arguments.defaults)


def count_function_max_arguments(arguments):
    """ returns maximum number of arguments. If uncertain, returns -1. """
    if arguments.vararg or arguments.kwarg:
        return -1
    return len(arguments.args) + len(arguments.kwonlyargs)


def count_function_arguments(arguments):
    """ returns minimum and maximum number of arguments. 
    If uncertain, the maximum is -1. """
    return count_function_min_arguments(arguments), count_function_max_arguments(arguments)


def count_call_arguments(call):
    """ returns the number of arguments given to call, and 
    a bool indicating whether that may be a lower limit """
    may_have_more = False
    min_call_args = 0
    for arg in call.args:
        if isinstance(arg, ast.Starred):
            # should not count *args
            may_have_more |= True
            continue
        min_call_args += 1
    for arg in call.keywords:
        if arg.arg is None:  # **kwargs
            may_have_more |= True
        min_call_args += 1
    return min_call_args, may_have_more


class FuncLister(ast.NodeVisitor):
    """Compiles a list of all functions and class inits
    with their call signatures.
    
    Result is in the known_functions attribute."""
    def __init__(self, filename):
        self.filename = filename
        self.known_functions = {}
        self.known_staticmethods = {}

    def visit_FunctionDef(self, node):
        is_staticmethod = len(node.decorator_list) == 1 and isinstance(node.decorator_list[0], ast.Name) and node.decorator_list[0].id == 'staticmethod'
        if node.decorator_list == [] or is_staticmethod:
            min_args = count_function_min_arguments(node.args)
            max_args = count_function_max_arguments(node.args)
        else:
            min_args = 0
            max_args = -1
        
        if node.name in self.known_functions:
            min_args_orig, max_args_orig = self.known_functions[node.name]
            min_combined_args = min(min_args, min_args_orig)
            if max_args == -1 or max_args_orig == -1:
                max_combined_args = -1
            else:
                max_combined_args = max(max_args, max_args_orig)
        else:
            min_combined_args, max_combined_args = min_args, max_args
        if is_staticmethod:
            self.known_staticmethods[node.name] = (min_combined_args, max_combined_args)
        else:
            self.known_functions[node.name] = (min_combined_args, max_combined_args)
        
        print('function "%s" has %d..%d arguments' % (node.name, min_args, max_args))
        self.generic_visit(node)
    
    def visit_ClassDef(self, node):
        # find the child that defines __init__
        if node.decorator_list == []:
            if node.name in self.known_functions:
                sys.stderr.write('%s:%d: ERROR: Class "%s" redefined\n' % (
                    self.filename, node.lineno, node.name))
                sys.exit(1)
            
            for child in ast.iter_child_nodes(node):
                # look for __init__ method:
                if not isinstance(child, ast.FunctionDef):
                    continue
                if not child.name == '__init__': 
                    continue
                
                arguments = child.args
                if len(arguments.args) >= 1 and arguments.args[0].arg == 'self':
                    min_args, max_args = count_function_arguments(arguments)
                    # remove self from arguments, as it is supplied by Python
                    if max_args > 0:
                        max_args -= 1
                    min_args -= 1
                    self.known_functions[node.name] = (min_args, max_args)
                    print('class "%s" init has %d..%d arguments' % (node.name, min_args, max_args))
        self.generic_visit(node)


class CallLister(ast.NodeVisitor):
    """Verifies all calls against call signatures in known_functions.
    Unknown functions are not verified."""
    def __init__(self, filename, known_functions):
        self.filename = filename
        self.known_functions = known_functions

    def visit_Call(self, node):
        self.generic_visit(node)
        if not isinstance(node.func, ast.Name):
            return
        
        funcname = node.func.id
        if funcname not in self.known_functions:
            return
        min_args, max_args = self.known_functions[funcname]
        min_call_args, may_have_more = count_call_arguments(node)
        
        if max_args >= 0 and min_call_args > max_args:
            sys.stderr.write('%s:%d: ERROR: Function "%s" (%d..%d arguments) called with too many (%d%s) arguments\n' % (
                self.filename, node.lineno, funcname, min_args, max_args, min_call_args, '+' if may_have_more else ''))
            sys.exit(1)
        elif min_call_args < min_args and not may_have_more:
            sys.stderr.write('%s:%d: ERROR: Function "%s" (%d..%d arguments) called with too few (%d%s) arguments\n' % (
                self.filename, node.lineno, funcname, min_args, max_args, min_call_args, '+' if may_have_more else ''))
            sys.exit(1)
        else:
            print("call(%s with %d%s args): OK" % (funcname, min_call_args, '+' if may_have_more else ''))
