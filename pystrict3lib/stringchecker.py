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


class StrFormatLister(ast.NodeVisitor):
    """ Check string interpolation """
    def __init__(self, filename):
        self.filename = filename

    def visit_BinOp(self, node):
        # handle %-style strings
        if isinstance(node.op, ast.Mod) and isinstance(node.left, ast.Str) and isinstance(node.right, ast.Tuple):
            formatter = node.left.s
            nargs = len(node.right.elts)
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
            if nargs != nelements:
                sys.stderr.write('%s:%d: ERROR: String interpolation "%s" (%d arguments) used with %d arguments\n' % (
                    self.filename, node.lineno, formatter, nelements, nargs))
                sys.exit(1)
            else:
                print("String interpolation ('%(fmt)s', %(nelements)d args) with %(nargs)d args: OK" % dict(
                    fmt=formatter, nelements=nelements, nargs=nargs))
        self.generic_visit(node)

    def visit_Call(self, node):
        # handle str.format style strings
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

            elements = [
                field_name.split('.')[0]
                for literal_text, field_name, format_spec, conversion in strformatter.parse(formatter)
                if (field_name, format_spec, conversion) != (None, None, None)
            ]
            if elements == [''] * len(elements):
                # unnamed, just need to count
                if nargs != len(elements):
                    sys.stderr.write('{}:{:d}: ERROR: String interpolation "{}" ({:d} arguments) used with {} arguments\n'.format(
                        self.filename, node.lineno, formatter, len(elements), nargs))
                    sys.exit(1)
                print("String interpolation ('{}', {nargs} args) with {ncallargs} args: OK".format(
                    formatter, nargs=nargs, ncallargs=len(elements)))
                return
            try:
                max_field = max(int(field_name) for field_name in elements if field_name != '')
                if nargs < max_field:
                    sys.stderr.write('{0}:{1:d}: ERROR: String interpolation "{2}" used with {3} arguments, but needs up to index {4:d}\n'.format(
                        self.filename, node.lineno, formatter, nargs, max_field))
                    sys.exit(1)
                print("String interpolation ('{}', up to field index {}) with {ncallargs} args: OK".format(
                    formatter, max_field, ncallargs=len(elements)))
                return
            except ValueError:
                pass
            
            keys_needed = {field_name for field_name in elements if field_name != ''}
            keys_supplied = {arg.arg for arg in node.keywords}
            
            if len(keys_needed - keys_supplied) > 0:
                sys.stderr.write('{}:{:d}: ERROR: String interpolation "{}" is missing keys {}\n'.format(
                    self.filename, node.lineno, formatter, keys_needed - keys_supplied))
                sys.exit(1)

            print("String interpolation ('{}') called with all {:d} keywords: OK".format(
                formatter, len(keys_needed)))
