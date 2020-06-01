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
import pprintast
import string

import pyparsing as pp

# from https://docs.python.org/3/library/stdtypes.html?highlight=string%20interpolation#printf-style-string-formatting
PCT, LPAREN, RPAREN, DOT = map(pp.Literal, '%().')
conversion_flag_expr = pp.oneOf(list("#0- +"))
conversion_type_expr = pp.oneOf(list("diouxXeEfFgGcrsa"))
length_mod_expr = pp.oneOf(list("hlL"))
interp_expr = (
    PCT
    + pp.Optional(LPAREN + pp.Word(pp.printables, excludeChars=")")("mapping_key") + RPAREN)
    + pp.Optional(conversion_flag_expr("conversion_flag"))
    + pp.Optional(('*' | pp.pyparsing_common.integer)("min_width"))
    + pp.Optional(DOT + ('*' | pp.pyparsing_common.integer)("max_width"))
    + pp.Optional(length_mod_expr("length_modifier"))
    + conversion_type_expr("conversion_type")
)

strformatter = string.Formatter()

preknown = set(builtins.__dict__).union({'__doc__', '__file__', '__name__', '__annotations__', '__dict__', '__builtins__'})
known_functions = dict()

class StrFormatLister(ast.NodeVisitor):
    def visit_BinOp(self, node):
        if isinstance(node.op, ast.Mod) and isinstance(node.left, ast.Str) and isinstance(node.right, ast.Tuple):
            formatter = node.left.s
            nargs = len(node.right.elts)
            # this is for str.format():
            #nelements = strformatter.parse(formatter)
            elements = list(interp_expr.scanString(formatter))
            nelements = 0
            for el, _, _ in elements:
                nelements += 1
                try:
                    if '*' in el.max_width:
                        nelements += 1
                except TypeError:
                    pass
                try:
                    if '*' in el.min_width:
                        nelements += 1
                except TypeError:
                    pass
            #pprintast.pprintast(node)
            #print(formatter, nelements, nargs, elements)
            if nargs != nelements:
                sys.stderr.write('%s:%d: ERROR: String interpolation "%s" (%d arguments) used with %d arguments\n' % (
                    filename, node.lineno, formatter, nelements, nargs))
                sys.exit(1)
            else:
                print("String interpolation ('%(fmt)s', %(nelements)d args) with %(nargs)d args: OK" % dict(
                    fmt=formatter, nelements=nelements, nargs=nargs))
        #print('function "%s" has %d..%d arguments' % (node.name, min_args, max_args))
        self.generic_visit(node)

    def visit_Call(self, node):
        self.generic_visit(node)
        if isinstance(node.func, ast.Attribute) and isinstance(node.func.value, ast.Str) and node.func.attr == 'format':
            formatter = node.func.value.s.strip()
            nargs = 0
            for arg in node.args:
                if isinstance(arg, ast.Starred):
                    # give up: called with *args, cannot count
                    return
                nargs += 1
            for arg in node.keywords:
                if arg.arg is None:
                    # give up: called with **kwargs, cannot count
                    return

            elements = [field_name
                for literal_text, field_name, format_spec, conversion in strformatter.parse(formatter)
                if (field_name, format_spec, conversion) != (None, None, None)]
            if elements == [''] * len(elements):
                # unnamed, just need to count
                if nargs != len(elements):
                    sys.stderr.write('{}:{:d}: ERROR: String interpolation "{}" ({:d} arguments) used with {} arguments\n'.format(filename, node.lineno, formatter, len(elements), nargs))
                    sys.exit(1)
                print("String interpolation ('{}', {nargs} args) with {ncallargs} args: OK".format(
                    formatter, nargs=nargs, ncallargs=len(elements)))
                return
            try:
                max_field = max(int(field_name) for field_name in elements)
                if nargs < max_field:
                    sys.stderr.write('{}:{:d}: ERROR: String interpolation "{}" used with {} arguments, but needs up to index {:d}\n'.format(filename, node.lineno, formatter, nargs, max_field))
                    sys.exit(1)
                print("String interpolation ('{}', up to field index {}) with {ncallargs} args: OK".format(
                    formatter, max_field, ncallargs=len(elements)))
                return
            except ValueError:
                pass
            
            #pprintast.pprintast(node)
            keys_needed = {field_name.split('.')[0] for field_name in elements if field_name != ''}
            keys_supplied = {arg.arg for arg in node.keywords}
            
            if len(keys_needed - keys_supplied) > 0:
                sys.stderr.write('{}:{:d}: ERROR: String interpolation "{}" is missing keys {}\n'.format(filename, node.lineno, formatter, keys_needed - keys_supplied))
                sys.exit(1)

            print("String interpolation ('{}') called with all {:d} keywords: OK".format(
                formatter, len(keys_needed)))
            
            return
            print("{0}{1}{0}".format(nargs, len(elements)))

class FuncLister(ast.NodeVisitor):
    def visit_FunctionDef(self, node):
        min_args = 0
        max_args = -1
        arguments = node.args
        #pprintast.pprintast(node)
        if node.decorator_list == []:
            min_args = 0
            max_args = 0
            optional_args_start = len(arguments.args) - len(arguments.defaults)
            for i, arg in enumerate(arguments.args):
                max_args += 1
                if arguments.vararg:
                    max_args = -1
                    break
                elif arguments.kw_defaults and arg in [getattr(arg2, 'n', getattr(arg2, 'id', None)) for arg2 in arguments.kw_defaults if arg2 is not None]:
                    pass
                elif i < optional_args_start:
                    min_args += 1
            if arguments.vararg or arguments.kwarg:
                max_args = -1
            else:
                max_args += len(arguments.kwonlyargs)
        
        if node.name in known_functions:
            min_args_orig, max_args_orig = known_functions[node.name]
            min_args = min(min_args, min_args_orig)
            if max_args == -1 or max_args_orig == -1:
                max_args = -1
            else:
                max_args = max(max_args, max_args_orig)
        known_functions[node.name] = (min_args, max_args)
        print('function "%s" has %d..%d arguments' % (node.name, min_args, max_args))
        self.generic_visit(node)

class CallLister(ast.NodeVisitor):
    def visit_Call(self, node):
        self.generic_visit(node)
        if not isinstance(node.func, ast.Name):
            return
        
        #pprintast.pprintast(node)
        #print(type(node), type(node.func))
        funcname = node.func.id
        if funcname not in known_functions:
            return
        min_args, max_args = known_functions[funcname]
        nargs = 0
        for arg in node.args:
            if isinstance(arg, ast.Starred):
                # give up
                return
            nargs += 1
        for arg in node.keywords:
            nargs += 1
        
        if max_args >= 0 and nargs > max_args or nargs < min_args:
            sys.stderr.write('%s:%d: ERROR: Function "%s" (%d..%d arguments) called with %d arguments\n' % (filename, node.lineno, funcname, min_args, max_args, nargs))
            sys.exit(1)
        else:
            print("call(%s with %d args): OK" % (funcname, nargs))


def flat_walk(node):
    #print(node)
    yield node
    if not isinstance(node, ast.FunctionDef) and not isinstance(node, ast.ClassDef) and not isinstance(node, ast.Lambda) and not isinstance(node, ast.Import) and not isinstance(node, ast.ImportFrom):
        for child in ast.iter_child_nodes(node):
            #print(node, child)
            yield from flat_walk(child)

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

def assert_unknown(name, node, filename):
    assert name is not None
    if name in known:
        sys.stderr.write('%s:%d: ERROR: Variable reuse: "%s"\n' % (filename, node.lineno, name))
        sys.exit(1)

asts = []
for filename in sys.argv[1:]:
    a = ast.parse(open(filename).read())

    StrFormatLister().visit(a)
    FuncLister().visit(a)
    asts.append((filename, a))

for filename, a in asts:
    known = set(preknown)

    CallLister().visit(a)
    
    for node in a.body:
        #print()
        #print(node)
        #pprintast.pprintast(node)
        #print(known - set(builtins.__dict__))
        #print(''.join(open(sys.argv[1]).readlines()[node.lineno-3:node.lineno+2]))
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
                    assert_unknown(name, node, filename)
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
                            assert_unknown(id, node, filename)
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
                        assert_unknown(id, node, filename)
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
                        assert_unknown(id, node, filename)
                        add_here.add(id)
                        forget_here.add(id)
                del target, generators
            if hasattr(el, 'name'):
                if el.name is not None:
                    assert_unknown(el.name, node, filename)
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

#print(known - preknown)


