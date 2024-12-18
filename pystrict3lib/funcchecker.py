#!/usr/bin/env python3
"""
Functions for checking the number of arguments of a function,
verifying function calls to them, and checking the docstrings.
"""

import ast
import builtins
import distutils.sysconfig
import importlib
import inspect
import logging
import os
import sys
from collections import defaultdict

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


def parse_builtin_signature(signature):
    """Get minimum and maximum number of arguments.

    :param signature: builtin function signature
    :returns: min, max (or -1 if unknown)
    """
    min_args = 0
    for param in signature.parameters.values():
        if (
            param.kind == inspect.Parameter.POSITIONAL_OR_KEYWORD
            or param.kind == inspect.Parameter.POSITIONAL_ONLY
        ):
            if param.default == inspect.Parameter.empty:
                min_args += 1
        else:
            break
        del param
    for param in signature.parameters.values():
        if (
            param.kind == inspect.Parameter.VAR_KEYWORD
            or param.kind == inspect.Parameter.VAR_POSITIONAL
        ):
            return min_args, -1

    max_args = len(signature.parameters)
    return min_args, max_args


def count_function_min_arguments(arguments):
    """Count minimum number of arguments."""
    return len(arguments.args) - len(arguments.defaults)


def count_function_max_arguments(arguments):
    """Count maximum number of arguments.

    If uncertain, returns -1.
    """
    if arguments.vararg or arguments.kwarg:
        return -1
    return len(arguments.args) + len(arguments.kwonlyargs)


def count_function_arguments(arguments):
    """Count minimum and maximum number of arguments.

    If uncertain, the maximum is -1.
    """
    return count_function_min_arguments(arguments), count_function_max_arguments(
        arguments
    )


def count_call_arguments(call):
    """Count the number of arguments given to call, and whether that may be a lower limit."""
    may_have_more = False
    min_call_args = 0
    for arg in call.args:
        if isinstance(arg, ast.Starred):
            # should not count *args
            may_have_more |= True
            continue
        min_call_args += 1
        del arg
    for arg in call.keywords:
        if arg.arg is None:  # **kwargs
            may_have_more |= True
        min_call_args += 1
    return min_call_args, may_have_more


def strip_left_indent(s):
    """Strip left padding of a multiline string `s`.

    :param s: string
    """
    body_lines = s.split("\n")
    filled_lines = [line for line in body_lines if line.strip() != ""]
    left_padding_to_remove = min(
        len(line) - len(line.lstrip()) for line in filled_lines
    )
    return "\n".join(
        [
            "" if line.strip() == "" else line[left_padding_to_remove:]
            for line in body_lines
        ]
    )


def list_documented_parameters(docstring):
    """Extract a list of documented parameters from docstring.

    Supports numpydoc-style, google-style and rst-style formats.

    Parameters
    ----------
    docstring: str
        documentation string

    Returns
    -------
    parameters: list
        names of the parameters
    types: list
        types of the parameters
    descriptions: list
        description of the parameters
    """
    params = []
    params_types = []
    params_docs = []
    for section_start, section_end in [
        ("\nParameters\n---------", "\n---"),
        ("\nOther Parameters\n---------", "\n---"),
        ("\nArgs:", "\n\n"),
    ]:
        if section_start in docstring:
            index_param_section = docstring.index(section_start) + len(section_start)
            try:
                index_next_section = docstring.index(section_end, index_param_section)
            except ValueError:
                index_next_section = -1
            parameter_section = strip_left_indent(
                docstring[index_param_section:index_next_section]
            )
            for line in parameter_section.split("\n"):
                if (
                    not line.startswith(" ")
                    and not line.startswith("\t")
                    and ":" in line
                ):
                    params.append(line.split(":")[0].strip())
                    params_types.append(line.split(":", maxsplit=1)[1].strip())
                    params_docs.append("")
                elif len(params_docs) > 0:
                    params_docs[-1] = (params_docs[-1].strip() + " " + line).strip()
    for line in docstring.split("\n"):
        if ":param " in line:
            param_name = line.split(":param ")[1].split(":", maxsplit=1)[0].strip()
            param_type = ''
            if len(param_name.split()) == 2:
                param_name, param_type = param_name.split()
            params.append(param_name)
            params_types.append(param_type)
            params_docs.append(line.split(":param ")[1].split(":", maxsplit=1)[1].strip())
    return params, params_types, params_docs


def max_documented_returns(docstring):
    """Extract a list of documented return values from docstring.

    For numpydoc-style, get the number.
    google-style and rst-style formats do not provide this.

    Parameters
    ----------
    docstring: str
        documentation string

    Returns
    -------
    max_returns: int | None
        None if unsure, int if the maximum number could be determined.
    """
    if "\n" not in docstring:
        return 0
    docstring_lstripped = strip_left_indent("\n".join(docstring.split("\n")[1:]))
    section_start = "\nReturns\n---------"
    section_end = "\n---"
    if section_start in docstring_lstripped:
        index_param_section = docstring_lstripped.index(section_start) + len(
            section_start
        )
        try:
            index_next_section = docstring_lstripped.index(
                section_end, index_param_section
            )
        except ValueError:
            index_next_section = -1
        return_section = strip_left_indent(
            docstring_lstripped[index_param_section:index_next_section]
        )
        # simply count non-indented lines, because name is optional
        entries = [
            line
            for line in return_section.split("\n")
            if not line.startswith(" ")
            and not line.startswith("\t")
            and not line.strip() == ""
        ]
        # some return types could be optional, but we expect at least one
        return len(entries)


class FuncLister(ast.NodeVisitor):
    """Compiles a list of all functions and class inits with their call signatures.

    Result is in the known_functions attribute.
    """

    def __init__(self, filename):
        """
        :param filename: file name
        """
        self.filename = filename
        self.known_functions = dict(**FuncLister.KNOWN_BUILTIN_FUNCTIONS)
        self.known_staticmethods = {}
        self.log = logging.getLogger("pystrict3.funcchecker")

    KNOWN_BUILTIN_FUNCTIONS = {}

    @staticmethod
    def load_builtin_functions():
        for f, func in builtins.__dict__.items():
            if inspect.isbuiltin(func) or inspect.isfunction(func):
                try:
                    FuncLister.KNOWN_BUILTIN_FUNCTIONS[f] = parse_builtin_signature(
                        inspect.signature(func)
                    )
                except ValueError:
                    FuncLister.KNOWN_BUILTIN_FUNCTIONS[f] = 0, -1

    def visit_FunctionDef(self, node):
        is_staticmethod = (
            len(node.decorator_list) == 1
            and isinstance(node.decorator_list[0], ast.Name)
            and node.decorator_list[0].id == "staticmethod"
        )
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

        self.log.debug(
            'function "%s" has %d..%d arguments' % (node.name, min_args, max_args)
        )
        self.generic_visit(node)

    def visit_ClassDef(self, node):
        # find the child that defines __init__
        if node.decorator_list == []:
            if node.name in self.known_functions:
                sys.stderr.write(
                    '%s:%d: ERROR: Class "%s" redefined\n'
                    % (self.filename, node.lineno, node.name)
                )
                sys.exit(1)

            for child in ast.iter_child_nodes(node):
                # look for __init__ method:
                if not isinstance(child, ast.FunctionDef):
                    continue
                if not child.name == "__init__":
                    continue

                arguments = child.args
                if len(arguments.args) >= 1 and arguments.args[0].arg == "self":
                    min_args, max_args = count_function_arguments(arguments)
                    # remove self from arguments, as it is supplied by Python
                    if max_args > 0:
                        max_args -= 1
                    min_args -= 1
                    self.known_functions[node.name] = (min_args, max_args)
                    self.log.debug(
                        'class "%s" init has %d..%d arguments'
                        % (node.name, min_args, max_args)
                    )

        self.generic_visit(node)


class CallLister(ast.NodeVisitor):
    """Verify calls against call signatures in known_functions."""

    def __init__(self, filename, known_functions):
        """
        :param filename: file name
        :param known_functions: dict of function names with number of arguments (min, max).

        Unknown functions are not verified.
        """
        self.filename = filename
        self.known_functions = known_functions
        self.log = logging.getLogger("pystrict3.funcchecker")
        self.checked_calls = 0

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
            sys.stderr.write(
                '%s:%d: ERROR: Function "%s" (%d..%d arguments) called with too many (%d%s) arguments\n'
                % (
                    self.filename,
                    node.lineno,
                    funcname,
                    min_args,
                    max_args,
                    min_call_args,
                    "+" if may_have_more else "",
                )
            )
            sys.exit(1)
        elif min_call_args < min_args and not may_have_more:
            sys.stderr.write(
                '%s:%d: ERROR: Function "%s" (%d..%d arguments) called with too few (%d%s) arguments\n'
                % (
                    self.filename,
                    node.lineno,
                    funcname,
                    min_args,
                    max_args,
                    min_call_args,
                    "+" if may_have_more else "",
                )
            )
            sys.exit(1)
        else:
            self.log.debug(
                "call(%s with %d%s args): OK"
                % (funcname, min_call_args, "+" if may_have_more else "")
            )
            self.checked_calls += 1


BUILTIN_MODULES = []
for m in list(sys.builtin_module_names) + list(sys.modules.keys()):
    if not m.startswith("_"):
        BUILTIN_MODULES.append(m)


class ModuleCallLister(ast.NodeVisitor):
    """Verifies all calls against call signatures in known_functions.
    Unknown functions are not verified."""

    def __init__(self, filename, load_policy="none"):
        """Initialize.

        :param filename: file name
        :param load_policy: if 'none', do not load any new modules.
            if 'builtins', load python libraries from the python
            standard library path. if 'all', try to load arbitrary
            python libraries as they are imported.
        """

        self.filename = filename
        self.checked_calls = 0

        if load_policy not in ("none", "builtins", "all"):
            raise ValueError(
                "load_policy needs to be one of ('none', 'builtins', 'all'), not '%s'"
                % load_policy
            )
        self.load_policy = load_policy
        self.approved_module_names = {
            k for k in sys.modules.keys() if not k.startswith("_")
        }

        if self.load_policy != "none":
            self.approved_module_names |= {
                k for k in sys.builtin_module_names if not k.startswith("_")
            }

        # if self.load_policy != 'all':
        #     print("allowed modules:", sorted(self.approved_module_names))
        self.used_module_names = {}
        self.log = logging.getLogger("pystrict3.funcchecker")

    def visit_Import(self, node):
        for alias in node.names:
            if alias.asname is None:
                self.used_module_names[alias.name] = alias.name
                # print('+module: "%s"' % (alias.name))
            else:
                self.used_module_names[alias.asname] = alias.name
                # print('+module: "%s"' % (alias.name))
            self.load_module(alias.name)
        self.generic_visit(node)

    def visit_ImportFrom(self, node):
        if node.level == 0:
            for alias in node.names:
                if alias.asname is None:
                    self.used_module_names[alias.name] = node.module + "." + alias.name
                    # print('+module: %s' % (node.module + '.' + alias.name, alias.name))
                else:
                    self.used_module_names[alias.asname] = (
                        node.module + "." + alias.name
                    )
                    # print('+module: %s' % (node.module + '.' + alias.name, alias.asname))
                self.load_module(node.module + "." + alias.name)
        self.generic_visit(node)

    # lazy load the needed module functions
    KNOWN_CALLS = defaultdict(dict)
    KNOWN_MODULES = {}

    def load_module(self, module_name):
        """Load python module and store all function call signatures.

        :param module_name: name of the module
        """
        # if this is a submodule, try to handle by importing the parent
        parts = module_name.split(".")
        parent_module = ".".join(parts[:-1])
        if parent_module != "":
            self.load_module(parent_module)
            parent_mod = ModuleCallLister.KNOWN_MODULES.get(parent_module)
            if parent_mod is not None:
                mod = getattr(parent_mod, parts[-1], None)
                if mod is not None:
                    ModuleCallLister.KNOWN_MODULES[module_name] = mod
                    return mod
                del mod

        if module_name in ModuleCallLister.KNOWN_MODULES:
            return ModuleCallLister.KNOWN_MODULES[module_name]

        ModuleCallLister.KNOWN_MODULES[module_name] = None
        if (
            self.load_policy != "all"
            and module_name.split(".")[0] not in self.approved_module_names
        ):
            return

        if self.load_policy == "builtins":
            if module_name.split(".")[0] not in self.approved_module_names:
                std_lib = distutils.sysconfig.get_python_lib(standard_lib=True)
                loadable_std_file = os.path.exists(
                    os.path.join(std_lib, module_name.split(".")[0] + ".py")
                )
                loadable_std_dir = os.path.exists(
                    os.path.join(std_lib, module_name.split(".")[0], "__init__.py")
                )
                if not loadable_std_file and not loadable_std_dir:
                    # do not load arbitrary modules
                    self.log.debug(
                        'skipping loading module "%s" outside standard lib'
                        % module_name
                    )
                    return

        try:
            self.log.info("+loading module %s" % module_name)
            mod = importlib.import_module(module_name)
            ModuleCallLister.KNOWN_MODULES[module_name] = mod
            return mod
        except ImportError:
            self.log.warning("WARNING: loading module %s failed" % module_name)
            return None

    def get_function(self, module_name, funcname):
        """Get a function from a module as a python object.

        :param module_name: name of the module
        :param funcname: function name
        """
        mod = ModuleCallLister.KNOWN_MODULES[module_name]
        assert mod is not None

        if funcname != "":
            for level in funcname.split("."):
                subm = getattr(mod, level, None)
                if subm is None:
                    self.log.debug(
                        'skipping unknown function "%s.%s"' % (module_name, level)
                    )
                    return
                else:
                    del mod
                    mod = subm

        return mod

    def lazy_load_call(self, module_name, funcname):
        """Get min and max function from a module as a python object.

        :param module_name: name of the module
        :param funcname: function name
        :returns: min, max
        """
        functions = ModuleCallLister.KNOWN_CALLS[module_name]
        if funcname in functions:
            # use cached result
            return functions[funcname]

        func = self.get_function(module_name, funcname)

        if inspect.isbuiltin(func) or inspect.isfunction(func):
            try:
                min_args, max_args = parse_builtin_signature(inspect.signature(func))
                self.log.debug(
                    '+function: "%s.%s" (%d..%d) arguments'
                    % (module_name, funcname, min_args, max_args)
                )
            except ValueError:
                min_args, max_args = 0, -1
                self.log.debug(
                    '+uninspectable callable: "%s.%s"' % (module_name, funcname)
                )
        elif inspect.isclass(func):
            min_args, max_args = parse_builtin_signature(
                inspect.signature(func.__init__)
            )
            # remove self from arguments, as it is supplied by Python
            if max_args > 0:
                max_args -= 1
            min_args -= 1
            self.log.debug(
                '+class: "%s.%s" (%d..%d) arguments'
                % (module_name, funcname, min_args, max_args)
            )
        elif callable(func):
            # some type we do not understand, like numpy ufuncs
            min_args, max_args = 0, -1
            self.log.debug('+uninspectable callable: "%s.%s"' % (module_name, funcname))
        else:
            # not callable
            return

        functions[funcname] = min_args, max_args
        return min_args, max_args

    def visit_Call(self, node):
        self.generic_visit(node)
        if isinstance(node.func, ast.Name):
            funcname = ""
            module_alias = node.func.id
            module_name = self.used_module_names.get(module_alias)
        elif not isinstance(node.func, ast.Attribute):
            # print("skipping call: not an attribute")
            return
        elif isinstance(node.func.value, ast.Name):
            funcname = node.func.attr
            module_alias = node.func.value.id
            module_name = self.used_module_names.get(module_alias)
        elif isinstance(node.func.value, ast.Attribute) and isinstance(
            node.func.value.value, ast.Name
        ):
            module_alias = node.func.value.value.id + "." + node.func.value.attr
            funcname = node.func.attr
            module_name = self.used_module_names.get(module_alias)
            if (
                module_name is None
                and node.func.value.value.id in self.used_module_names
            ):
                module_name = self.used_module_names.get(node.func.value.value.id)
                funcname = node.func.value.attr + "." + node.func.attr
        else:
            # print("skipping call: not an 1 or 2-layer attribute: %s")
            return

        if module_name is None or module_name not in ModuleCallLister.KNOWN_MODULES:
            # print('skipping module "%s", because not registered' % module_alias)
            return

        del module_alias
        if (
            self.load_policy in ("builtin", "none")
            and module_name not in self.approved_module_names
        ):
            self.log.debug('skipping call into unapproved module "%s"' % module_name)
            return

        if ModuleCallLister.KNOWN_MODULES[module_name] is None:
            self.log.debug('skipping call into not loaded module "%s"' % module_name)
            return

        if self.get_function(module_name, funcname) is None:
            sys.stderr.write(
                '%s:%d: ERROR: "%s.%s" is not in a known module\n'
                % (self.filename, node.lineno, module_name, funcname)
            )
            sys.exit(1)

        signature = self.lazy_load_call(module_name, funcname)
        if signature is None:
            sys.stderr.write(
                '%s:%d: ERROR: "%s.%s" is not a known function\n'
                % (self.filename, node.lineno, module_name, funcname)
            )
            sys.exit(1)
            return

        min_args, max_args = signature
        min_call_args, may_have_more = count_call_arguments(node)

        if max_args >= 0 and min_call_args > max_args:
            sys.stderr.write(
                '%s:%d: ERROR: function "%s.%s" (%d..%d arguments) called with too many (%d%s) arguments\n'
                % (
                    self.filename,
                    node.lineno,
                    module_name,
                    funcname,
                    min_args,
                    max_args,
                    min_call_args,
                    "+" if may_have_more else "",
                )
            )
            sys.exit(1)
        elif min_call_args < min_args and not may_have_more:
            sys.stderr.write(
                '%s:%d: ERROR: function "%s.%s" (%d..%d arguments) called with too few (%d%s) arguments\n'
                % (
                    self.filename,
                    node.lineno,
                    module_name,
                    funcname,
                    min_args,
                    max_args,
                    min_call_args,
                    "+" if may_have_more else "",
                )
            )
            sys.exit(1)
        else:
            self.log.debug(
                "call(%s.%s with %d%s args): OK"
                % (module_name, funcname, min_call_args, "+" if may_have_more else "")
            )
            self.checked_calls += 1
