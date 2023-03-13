#!/usr/bin/env python3
"""gendocstr

Generates python numpy-style doc strings.
"""

import argparse
import logging
import sys
import textwrap

import redbaron

from pystrict3lib.funcchecker import list_documented_parameters

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


class HelpfulParser(argparse.ArgumentParser):
    def error(self, message):
        """report error to stderr.

        :param message: The message"""
        sys.stderr.write("error: %s\n" % message)
        self.print_help()
        sys.exit(2)


def modify_function(function):
    """Modify python function.

    Injects docstrings to document parameters and return values.

    Parameters
    -----------
    function: Node
        RedBaron full syntax tree node of a python function.
    """

    r = function
    print("Analying function: %s" % r.name)
    params = [a.target.value for a in r.arguments]
    # get type from annotation
    types = {
        a.target.value: a.annotation for a in r.arguments if a.annotation is not None
    }
    # guess type from assignment
    for a in r.arguments:
        if a.value is not None and a.target.value not in types:
            try:
                types[a.target.value] = type(a.value.to_python()).__name__
            except AttributeError:
                pass

    # load existing docstring, if any
    if r.value[0].type == "string":
        docstring = r.value[0].to_python()
        docstring_body = textwrap.dedent("\n".join(docstring.split("\n")[1:]))
        # indent_strings = [line[:len(line.lstrip())] for line in docstring.split("\n")[1:] if line.strip() != '']
        params_documented = list_documented_parameters(docstring_body)
    else:
        docstring = "<summary sentence of function in imperative>.\n\n"
        params_documented = []
    # list missing parameters
    params_missing = [p for p in params if p not in params_documented and p != "self"]

    if "\nParameters\n" not in docstring and len(params_missing) > 0:
        docstring += """
Parameters
-----------
"""
    for par in params_missing:
        docstring += "%s: %s\n    <MEANING OF %s>\n" % (
            par,
            types.get(par, "<TYPE>"),
            par,
        )
        del par

    return_statements = r.find_all("return")
    return_names = []
    for ret in return_statements:
        if ret.value is None:
            continue
        elif ret.value.type == "tuple":
            for n in ret.value.value:
                if n.type == "name":
                    name = n.value
                    if name not in return_names:
                        return_names.append(name)
                else:
                    if "<NAME>" not in return_names:
                        return_names.append("<NAME>")
        elif ret.value.type == "name":
            name = ret.value.value
            if name in ('True', 'False'):
                if r.name not in return_names:
                    return_names.append(r.name)
                    types[r.name] = 'bool'
            elif name not in return_names:
                return_names.append(name)
        else:
            if "<NAME>" not in return_names:
                return_names.append("<NAME>")
    if return_names == [] and len(return_statements) > 0:
        return_names.append("<NAME>")

    if "\Returns\n" not in docstring and len(return_names) > 0:
        docstring += """
Returns
----------
"""
        for par in return_names:
            docstring += "%s: %s\n    <MEANING OF %s>\n" % (
                par,
                types.get(par, "<TYPE>"),
                par,
            )
    if r.value[0].type == "string":
        r.value[0].value = '"""%s"""' % docstring
    else:
        r.value.insert(0, '"""%s"""' % docstring)


def main():
    """Parse command line arguments and analyse python file."""
    parser = HelpfulParser(
        description=__doc__,
        epilog="""Johannes Buchner (C) 2020-2023 <johannes.buchner.acad@gmx.com>""",
        formatter_class=argparse.ArgumentDefaultsHelpFormatter,
    )

    parser.add_argument(
        "--verbose",
        "-v",
        default=False,
        action="store_true",
        help="""More verbose logging output.""",
    )
    parser.add_argument(
        "--in-place",
        default=False,
        action="store_true",
        help="""Overwrite python file directly.""",
    )

    parser.add_argument("filename", type=str, help="""python file to parse""")

    args = parser.parse_args()

    logger = logging.getLogger("pystrict3")
    handler = logging.StreamHandler(sys.stderr)
    handler.setLevel(logging.DEBUG if args.verbose else logging.INFO)
    formatter = logging.Formatter("[%(levelname)s] %(message)s")
    handler.setFormatter(formatter)
    logger.addHandler(handler)
    logger.setLevel(logging.DEBUG if args.verbose else logging.INFO)

    rb = redbaron.RedBaron(open(args.filename).read())
    # find all function and method declarations
    results = rb.find_all("def")
    for r in results:
        modify_function(r)

    if args.in_place:
        outfile = args.filename
    else:
        outfile = args.filename.replace(".py", "-new.py")

    with open(outfile, "w") as fout:
        fout.write(rb.dumps())


# some test functions:

def foo(a: float, b: int):
    pass


def foo2(a: float, b: int):
    if False:
        return a
    else:
        return b


def bar(a: int, b=3, c=False):
    return a + b


def baz(a, b):
    return a, b, a + b, 3

def indicator(r):
    if r > 42:
        return False
    else:
        return True

class Foo(object):
    def __init__(self, a: int, b=3):
        pass
    def calc(self):
        return 42

if __name__ == "__main__":
    main()
