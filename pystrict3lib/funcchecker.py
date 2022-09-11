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
import inspect
import importlib
import builtins
import distutils.sysconfig
import os
from collections import defaultdict


def parse_builtin_signature(signature):
    min_args = 0
    for param in signature.parameters.values():
        if param.kind == inspect.Parameter.POSITIONAL_OR_KEYWORD or param.kind == inspect.Parameter.POSITIONAL_ONLY:
            if param.default == inspect.Parameter.empty:
                min_args += 1
        else:
            break
    for param in signature.parameters.values():
        if param.kind == inspect.Parameter.VAR_KEYWORD or param.kind == inspect.Parameter.VAR_POSITIONAL:
            return min_args, -1
    
    max_args = len(signature.parameters)
    return min_args, max_args


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

def strip_left_indent(s):
    body_lines = s.split('\n')
    filled_lines = [line for line in body_lines if line.strip() != '']
    left_padding_to_remove = min(len(line) - len(line.lstrip()) for line in filled_lines)
    return '\n'.join(['' if line.strip() == '' else line[left_padding_to_remove:] for line in body_lines])
    

def list_documented_parameters(docstring):
    """Extract a list of documented parameters from docstring

    support numpydoc-style, google-style and rst-style formats.
    
    Parameters
    -----------
    docstring: str
        documentation string
    
    Returns
    -------
    parameters: list
        names of the parameters
    """
    params = []
    if '\n' not in docstring:
        return params
    docstring_lstripped = strip_left_indent('\n'.join(docstring.split('\n')[1:]))
    for section_start, section_end in [
        ('\nParameters\n---------', '\n---'),
        ('\nOther Parameters\n---------', '\n---'),
        ('\nArgs:', '\n\n')
    ]:
        if section_start in docstring_lstripped:
            index_param_section = docstring_lstripped.index(section_start) + len(section_start)
            try:
                index_next_section = docstring_lstripped.index(section_end, index_param_section)
            except ValueError:
                index_next_section = -1
            parameter_section = strip_left_indent(docstring_lstripped[index_param_section:index_next_section])
            for line in parameter_section.split('\n'):
                if not line.startswith(' ') and not line.startswith('\t') and ':' in line:
                    params.append(line.split(':')[0].strip())
    for line in docstring.split('\n'):
        if ':param' in line:
            params.append(line.split(':param')[1].split(':')[0])
    return params

def max_documented_returns(docstring):
    """Extract a list of documented return values from docstring

    for numpydoc-style, get the number.
    google-style and rst-style formats do not provide this.
    
    Parameters
    -----------
    docstring: str
        documentation string
    
    Returns
    -------
    max_returns: int or None
        None if unsure, int if the maximum number could be determined.
    """
    params = []
    if '\n' not in docstring:
        return params
    docstring_lstripped = strip_left_indent('\n'.join(docstring.split('\n')[1:]))
    section_start = '\nReturns\n---------'
    section_end = '\n---'
    if section_start in docstring_lstripped:
        index_param_section = docstring_lstripped.index(section_start) + len(section_start)
        try:
            index_next_section = docstring_lstripped.index(section_end, index_param_section)
        except ValueError:
            index_next_section = -1
        return_section = strip_left_indent(docstring_lstripped[index_param_section:index_next_section])
        # simply count non-indented lines, because name is optional
        entries = [line for line in return_section.split('\n') if not line.startswith(' ') and not line.startswith('\t') and not line.strip() == '']
        # some return types could be optional, but we expect at least one
        return len(entries)

class FuncLister(ast.NodeVisitor):
    """Compiles a list of all functions and class inits
    with their call signatures.
    
    Result is in the known_functions attribute."""
    def __init__(self, filename):
        self.filename = filename
        self.known_functions = dict(**FuncLister.KNOWN_BUILTIN_FUNCTIONS)
        self.known_staticmethods = {}

    KNOWN_BUILTIN_FUNCTIONS = {}
    
    @staticmethod
    def load_builtin_functions():
        for f, func in builtins.__dict__.items():
            if inspect.isbuiltin(func) or inspect.isfunction(func):
                try:
                    FuncLister.KNOWN_BUILTIN_FUNCTIONS[f] = parse_builtin_signature(inspect.signature(func))
                except ValueError:
                    FuncLister.KNOWN_BUILTIN_FUNCTIONS[f] = 0, -1

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


BUILTIN_MODULES = []
for m in list(sys.builtin_module_names) + list(sys.modules.keys()):
    if not m.startswith('_'):
        BUILTIN_MODULES.append(m)


class ModuleCallLister(ast.NodeVisitor):
    """Verifies all calls against call signatures in known_functions.
    Unknown functions are not verified."""

    def __init__(self, filename, load_policy='none'):
        """ If load_policy is 'none', do not load any new modules.
        if load_policy is 'builtins', load python libraries from the python 
        standard library path.
        if load_policy is 'all', try to load arbitrary python libraries."""

        self.filename = filename

        if load_policy not in ('none', 'builtins', 'all'):
            raise ValueError("load_policy needs to be one of ('none', 'builtins', 'all'), not '%s'" % load_policy)
        self.load_policy = load_policy
        self.approved_module_names = {k for k in sys.modules.keys() if not k.startswith('_')}

        if self.load_policy != 'none':
            self.approved_module_names |= {k for k in sys.builtin_module_names if not k.startswith('_')}

        # if self.load_policy != 'all':
        #     print("allowed modules:", sorted(self.approved_module_names))
        self.used_module_names = {}

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
                    self.used_module_names[alias.name] = node.module + '.' + alias.name
                    # print('+module: %s' % (node.module + '.' + alias.name, alias.name))
                else:
                    self.used_module_names[alias.asname] = node.module + '.' + alias.name
                    # print('+module: %s' % (node.module + '.' + alias.name, alias.asname))
                self.load_module(node.module + '.' + alias.name)
        self.generic_visit(node)

    # lazy load the needed module functions
    KNOWN_CALLS = defaultdict(dict)
    KNOWN_MODULES = {}

    def load_module(self, module_name):
        # if this is a submodule, try to handle by importing the parent
        parts = module_name.split('.')
        parent_module = '.'.join(parts[:-1])
        if parent_module != '':
            self.load_module(parent_module)
            parent_mod = ModuleCallLister.KNOWN_MODULES.get(parent_module)
            if parent_mod is not None:
                mod = getattr(parent_mod, parts[-1], None)
                if mod is not None:
                    ModuleCallLister.KNOWN_MODULES[module_name] = mod
                    return mod
                del mod

        ModuleCallLister.KNOWN_MODULES[module_name] = None
        if self.load_policy != 'all' and module_name.split('.')[0] not in self.approved_module_names:
            return

        if self.load_policy == 'builtins':
            if module_name.split('.')[0] not in self.approved_module_names:
                std_lib = distutils.sysconfig.get_python_lib(standard_lib=True)
                loadable_std_file = os.path.exists(os.path.join(std_lib, module_name.split('.')[0] + '.py'))
                loadable_std_dir = os.path.exists(os.path.join(std_lib, module_name.split('.')[0], '__init__.py'))
                if not loadable_std_file and not loadable_std_dir:
                    # do not load arbitrary modules
                    print('skipping loading module "%s" outside standard lib' % module_name)
                    return

        try:
            print('+loading module %s' % module_name)
            mod = importlib.import_module(module_name)
            ModuleCallLister.KNOWN_MODULES[module_name] = mod
            return mod
        except ImportError:
            print('WARNING: loading module %s failed' % module_name)
            return None

    def get_function(self, module_name, funcname):
        mod = ModuleCallLister.KNOWN_MODULES[module_name]
        assert mod is not None

        if funcname != "":
            for level in funcname.split('.'):
                subm = getattr(mod, level, None)
                if subm is None:
                    print('skipping unknown function "%s.%s"' % (module_name, level))
                    return
                else:
                    del mod
                    mod = subm
        
        return mod

    def lazy_load_call(self, module_name, funcname):
        functions = ModuleCallLister.KNOWN_CALLS[module_name]
        if funcname in functions:
            # use cached result
            return functions[funcname]

        func = self.get_function(module_name, funcname)
        
        if inspect.isbuiltin(func) or inspect.isfunction(func):
            try:
                min_args, max_args = parse_builtin_signature(inspect.signature(func))
                print('+function: "%s.%s" (%d..%d) arguments' % (module_name, funcname, min_args, max_args))
            except ValueError:
                min_args, max_args = 0, -1
                print('+uninspectable callable: "%s.%s"' % (module_name, funcname))
        elif inspect.isclass(func):
            min_args, max_args = parse_builtin_signature(inspect.signature(func.__init__))
            # remove self from arguments, as it is supplied by Python
            if max_args > 0:
                max_args -= 1
            min_args -= 1
            print('+class: "%s.%s" (%d..%d) arguments' % (module_name, funcname, min_args, max_args))
        elif hasattr(func, '__call__'):
            # some type we do not understand, like numpy ufuncs
            min_args, max_args = 0, -1
            print('+uninspectable callable: "%s.%s"' % (module_name, funcname))
        else:
            # not callable
            return

        functions[funcname] = min_args, max_args
        return min_args, max_args

    def visit_Call(self, node):
        self.generic_visit(node)
        if isinstance(node.func, ast.Name):
            funcname = ''
            module_alias = node.func.id
            module_name = self.used_module_names.get(module_alias)
        elif not isinstance(node.func, ast.Attribute):
            # print("skipping call: not an attribute")
            return
        elif isinstance(node.func.value, ast.Name):
            funcname = node.func.attr
            module_alias = node.func.value.id
            module_name = self.used_module_names.get(module_alias)
        elif isinstance(node.func.value, ast.Attribute) and isinstance(node.func.value.value, ast.Name):
            module_alias = node.func.value.value.id + '.' + node.func.value.attr
            funcname = node.func.attr
            module_name = self.used_module_names.get(module_alias)
            if module_name is None and node.func.value.value.id in self.used_module_names:
                module_name = self.used_module_names.get(node.func.value.value.id)
                funcname = node.func.value.attr + '.' + node.func.attr
        else:
            # print("skipping call: not an 1 or 2-layer attribute: %s")
            return

        if module_name is None or module_name not in ModuleCallLister.KNOWN_MODULES:
            #print('skipping module "%s", because not registered' % module_alias)
            return

        del module_alias
        if self.load_policy in ('builtin', 'none') and module_name not in self.approved_module_names:
            print('skipping call into unapproved module "%s"' % module_name)
            return

        if ModuleCallLister.KNOWN_MODULES[module_name] is None:
            print('skipping call into not loaded module "%s"' % module_name)
            return

        if self.get_function(module_name, funcname) is None:
            sys.stderr.write('%s:%d: ERROR: "%s.%s" is not in a known module\n' % (
                self.filename, node.lineno, module_name, funcname))
            sys.exit(1)
            
        signature = self.lazy_load_call(module_name, funcname)
        if signature is None:
            sys.stderr.write('%s:%d: ERROR: "%s.%s" is not a known function\n' % (
                self.filename, node.lineno, module_name, funcname))
            sys.exit(1)
            return

        min_args, max_args = signature
        min_call_args, may_have_more = count_call_arguments(node)

        if max_args >= 0 and min_call_args > max_args:
            sys.stderr.write('%s:%d: ERROR: function "%s.%s" (%d..%d arguments) called with too many (%d%s) arguments\n' % (
                self.filename, node.lineno, module_name, funcname, 
                min_args, max_args, min_call_args, '+' if may_have_more else ''))
            sys.exit(1)
        elif min_call_args < min_args and not may_have_more:
            sys.stderr.write('%s:%d: ERROR: function "%s.%s" (%d..%d arguments) called with too few (%d%s) arguments\n' % (
                self.filename, node.lineno, module_name, funcname, 
                min_args, max_args, min_call_args, '+' if may_have_more else ''))
            sys.exit(1)
        else:
            print('call(%s.%s with %d%s args): OK' % (module_name, funcname, min_call_args, '+' if may_have_more else ''))
