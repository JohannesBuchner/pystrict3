#!/usr/bin/env python3
"""pystrict3: a Python code checker.

Checks number of arguments in function, class init and method calls.
Optionally also checks calls to imported modules.

Checks that class attributes accessed are assigned somewhere.

Checks that builtin names are not overwritten.

Checks that variables are only assigned once.

"""

import sys
import pystrict3lib
import argparse

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
        sys.stderr.write('error: %s\n' % message)
        self.print_help()
        sys.exit(2)


if __name__ == '__main__':

    parser = HelpfulParser(
        description=__doc__,
        epilog="""Johannes Buchner (C) 2020 <johannes.buchner.acad@gmx.com>""",
        formatter_class=argparse.ArgumentDefaultsHelpFormatter)

    parser.add_argument(
        '--import-builtin', action='store_true',
        help="""Also load builtin python modules to check function signatures.""")

    parser.add_argument(
        '--import-any', action='store_true',
        help="""Also load any modules specified in import statements to check function signatures.
        Warning: can execute arbitrary module code.""")

    parser.add_argument('filenames', type=str, nargs='+', help="""python files to parse""")

    args = parser.parse_args()

    module_load_policy = 'all' if args.import_any else 'builtins' if args.import_builtin else 'none'
    pystrict3lib.main(args.filenames, module_load_policy)
