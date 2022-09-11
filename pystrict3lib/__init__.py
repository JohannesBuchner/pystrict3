#!/usr/bin/env python3
"""
pystrict3: a Python3 code plausibility checker
"""

import ast
import sys
import builtins
import logging
import operator

from .funcchecker import FuncLister, list_documented_parameters, max_documented_returns, CallLister, ModuleCallLister
from .classchecker import ClassPropertiesLister

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

first_item_getter = operator.itemgetter(0)

preknown = set(builtins.__dict__).union({'__doc__', '__file__', '__name__', '__annotations__', '__dict__', '__builtins__'})


def get_arg_ids(node):
    """List variable names mentioned in a node."""
    if hasattr(node, 'args') and isinstance(node.args, ast.arguments):
        args = node.args
        for arg in args.args:
            yield arg.arg
        if hasattr(args, 'kwonlyargs'):
            for arg in args.kwonlyargs:
                yield arg.arg
        if getattr(args, 'vararg', None) is not None:
            yield args.vararg.arg
        if getattr(args, 'kwarg', None) is not None:
            yield args.kwarg.arg


def get_assigned_ids(node):
    """List variable names being assigned in a node."""
    if isinstance(node, ast.Name) and not isinstance(node.ctx, ast.Del):
        yield node.id
    if hasattr(node, 'target'):
        yield from get_assigned_ids(node.target)
    if hasattr(node, 'targets'):
        for target in node.targets:
            yield from get_assigned_ids(target)
    if hasattr(node, 'names'):
        for target in node.names:
            if target.asname is not None:
                yield target.asname
            else:
                yield target.name
    if hasattr(node, 'elts'):
        for el in node.elts:
            yield from get_assigned_ids(el)


def get_deleted_ids(node):
    """List variable names being deleted in a node."""
    if isinstance(node, ast.Name) and isinstance(node.ctx, ast.Del):
        yield node.id
    if hasattr(node, 'target'):
        yield from get_deleted_ids(node.target)
    if hasattr(node, 'targets'):
        for target in node.targets:
            yield from get_deleted_ids(target)


def is_container(node):
    """Check if node contains code."""
    return isinstance(node, ast.FunctionDef) or isinstance(node, ast.AsyncFunctionDef) or isinstance(node, ast.ClassDef) or isinstance(node, ast.Lambda) or isinstance(node, ast.Expr) or isinstance(node, ast.Call)


def get_all_ids(node):
    """Get all ids defined in names, tuples and targets here.

    :param node: AST node
    """
    if is_container(node):
        return
    if hasattr(node, 'name'):
        yield node.name.split('.')[0]
    if hasattr(node, 'id'):
        yield node.id
    if hasattr(node, 'target'):
        yield from get_all_ids(node.target)
    if hasattr(node, 'targets'):
        for target in node.targets:
            yield from get_all_ids(target)
    if hasattr(node, 'elts'):
        for el in node.elts:
            yield from get_all_ids(el)
    if hasattr(node, 'items'):
        for el in node.items:
            if el.optional_vars is not None:
                yield from get_all_ids(el.optional_vars)
    if hasattr(node, 'args'):
        if isinstance(node.args, ast.arguments):
            args = node.args
            for arg in args.args:
                yield arg.arg
            if hasattr(args, 'kwonlyargs'):
                for arg in args.kwonlyargs:
                    yield arg.arg
            if getattr(args, 'vararg', None) is not None:
                yield args.vararg.arg
            if getattr(args, 'kwarg', None) is not None:
                yield args.kwarg.arg
        else:
            for arg in node.args:
                yield from get_all_ids(arg)
    if hasattr(node, 'value') and not isinstance(node, ast.Attribute):
        yield from get_all_ids(node.value)


def block_terminates(statements):
    """Check if code block stops the execution."""
    for statement in statements:
        if isinstance(statement, ast.Return):
            return True
        if isinstance(statement, ast.Expr) and isinstance(statement.value, ast.Call) and isinstance(statement.value.func, ast.Attribute) and isinstance(statement.value.func.value, ast.Name):
            if statement.value.func.value.id == 'sys' and statement.value.func.attr == 'exit':
                return True
    return False


class FuncDocVerifier(ast.NodeVisitor):
    """Compares parameter names in function definition with docstring."""

    def __init__(self, filename):
        self.filename = filename
        self.log = logging.getLogger('pystrict3.funcdoc')
        self.undocumented_parameters_found = False
        self.undocumented_returns_found = False
        self.class_methods = []
        self.checked_docstrings = 0

    def visit_ClassDef(self, node):
        for child in ast.iter_child_nodes(node):
            # look for methods:
            if isinstance(child, ast.FunctionDef):
                self.class_methods.append(child)

    def visit_FunctionDef(self, node):
        arguments = node.args
        module_docstring = ast.get_docstring(node)
        if module_docstring is None:
            return

        documented_parameters = list_documented_parameters(module_docstring)
        function_arguments = [arg.arg for arg in arguments.args]
        if node in self.class_methods:
            arguments = function_arguments[1:]
        else:
            arguments = function_arguments
        del function_arguments
        if len(documented_parameters) == 0:
            if len(arguments) > 0:
                sys.stderr.write('%s:%d: WARNING: function "%s" does not have any parameter docs\n' % (
                    self.filename, node.lineno, node.name))
            return
        self.checked_docstrings += 1
        self.log.debug("documented parameters of %s: %s", node.name, ', '.join(documented_parameters))
        for arg in arguments:
            if arg not in documented_parameters:
                sys.stderr.write('%s:%d: ERROR: argument "%s" of "%s" missing in docstring\n' % (
                    self.filename, node.lineno, arg, node.name))
                self.undocumented_parameters_found |= True

        all_returns = [
            (return_tuple_length, return_node)
            for return_tuple_length, return_node in self._walk_tree(node.body)
            if return_tuple_length > 1]
        if len(all_returns) == 0:
            return
        return_tuple_length, return_node = max(all_returns, key=first_item_getter)
        if return_tuple_length > 1:
            # see if a return tuple is documented
            num_documented_returns = max_documented_returns(module_docstring) or 1
            self.log.debug("%s returns at most %s values; %d documented", node.name, return_tuple_length, num_documented_returns)
            if return_tuple_length > num_documented_returns:
                names = [getattr(el, 'id', 'var') for el in return_node.elts]
                if num_documented_returns == 1:
                    sys.stderr.write('%s:%d: WARNING: function "%s" may not document return of %d elements as in line %d: (%s)\n' % (
                        self.filename, node.lineno, node.name, return_tuple_length, return_node.lineno, ', '.join(names)))
                else:
                    sys.stderr.write('%s:%d: ERROR: function "%s" does not document return of %d elements as in line %d: (%s)\n' % (
                        self.filename, node.lineno, node.name, return_tuple_length, return_node.lineno, ', '.join(names)))
                    self.undocumented_returns_found |= True

    def _walk_tree(self, nodes):
        for node in nodes:
            if isinstance(node, ast.Return):
                yield len(getattr(node.value, 'elts', [])), node.value

            if hasattr(node, 'body'):
                body = node.body if isinstance(node.body, list) else [node.body]
                yield from self.walk_tree(body)

            if getattr(node, 'orelse', []) != []:
                yield from self.walk_tree(node.orelse)

            if getattr(node, 'finalbody', []) != []:
                yield from self.walk_tree(node.finalbody)


class NameAssignVerifier():
    """Verify name definitions and access.

    Makes sure variables that are defined have not been defined before,
    and variables being deleted have been defined before.

    :param filename: file name
    :param allow_variable_reuse: allow redefinition of variables
    """

    def __init__(self, filename, allow_variable_reuse=False):
        self.filename = filename
        self.log = logging.getLogger('pystrict3.nameassign')
        self.found_variable_unknown = False
        self.found_variable_reused = False
        self.allow_variable_reuse = allow_variable_reuse
        self.found_builtin_overwritten = False
        self.unknown_checked = 0
        self.known_checked = 0

    def variable_unknown_found(self, lineno, name):
        """Report a undefined variable `name` was found in line `lineno`."""
        sys.stderr.write('%s:%d: ERROR: Variable unknown: "%s"\n' % (self.filename, lineno, name))
        self.found_variable_unknown |= True
        raise Exception(name)

    def assert_unknown(self, name, known, lineno, override_with_builtins=False):
        """Report error if `name` is already in set `known`."""
        self.log.debug("assert_unknown: %s, %s", name, lineno)
        assert name is not None
        # the nested if allows deleting builtins and re-defining them afterwards
        if name in known:
            previous_state, _ = known[name]
            if name in preknown:
                if not override_with_builtins:
                    sys.stderr.write('%s:%d: ERROR: Overwriting builtin variable: "%s"\n' % (
                        self.filename, lineno, name))
                    self.found_builtin_overwritten |= True
            elif name == '_':
                # throwaway variable is allowed to be overridden
                pass
            elif previous_state is not None and previous_state:
                self.found_variable_reused |= True
                if self.allow_variable_reuse:
                    sys.stderr.write('%s:%d: WARNING: Variable "%s" set previously in line %d may have changed meaning\n' % (
                        self.filename, lineno, name, known[name][1]))
                else:
                    sys.stderr.write('%s:%d: ERROR: Variable "%s" set previously defined in line %d, is redefined here\n' % (
                        self.filename, lineno, name, known[name][1]))
        else:
            self.unknown_checked += 1

    def check_new_identifiers(self, elements, node, known):
        """Add newly defined variables and verify that the accessed ones are defined in known"""
        add = {}
        forget = set()
        self.log.debug('check_new_identifiers: known: %s', known.keys() - preknown)
        for el in elements:
            self.log.debug('check_new_identifiers: element %s', type(el).__name__)
            add_here = {}
            forget_here = set()
            # find all name nodes and look at ids
            if hasattr(el, 'names'):
                names = el.names
                for name in names:
                    if getattr(name, 'asname', None) is not None:
                        name = getattr(name, 'asname')
                    elif hasattr(name, 'name'):
                        name = name.name
                    self.log.debug('check_new_identifiers: name %s', name)
                    self.assert_unknown(
                        name, known, el.lineno,
                        override_with_builtins=getattr(node, 'module', '') == 'builtins')
                    name = name.split('.')[0]
                    add_here[name] = el.lineno
                del name, names
            if hasattr(el, 'targets'):
                targets = el.targets
                for target in targets:
                    self.log.debug('check_new_identifiers: target %s with ids: %s', target, set(get_assigned_ids(target)))
                    for name in get_assigned_ids(target):
                        if isinstance(getattr(target, 'ctx'), ast.Del):
                            self.log.debug('check_new_identifiers: del target name %s', name)
                            if name in add:
                                del add[name]
                            if name in add_here:
                                del add_here[name]
                            if name in known:
                                del known[name]
                            forget_here.add(name)
                        else:
                            self.log.debug('check_new_identifiers: add target name %s', name)
                            self.assert_unknown(name, known, el.lineno)
                            add_here[name] = el.lineno
                del target, targets
            if hasattr(el, 'items'):
                items = el.items
                for item in items:
                    self.log.debug('check_new_identifiers: item %s', item)
                    if item.optional_vars is None:
                        names = item.context_expr
                    else:
                        names = item.optional_vars
                    for name in get_all_ids(names):
                        self.assert_unknown(name, known, el.lineno)
                        add_here[name] = el.lineno
                    del names
                del item, items
            if hasattr(el, 'target') and not isinstance(el, ast.AugAssign):
                for name in get_assigned_ids(el.target):
                    self.log.debug('check_new_identifiers: target %s', name)
                    self.assert_unknown(name, known, el.lineno)
                    add_here[name] = node.lineno
            if hasattr(el, 'generators'):
                generators = el.generators
                for target in generators:
                    for name in get_assigned_ids(target):
                        self.log.debug('check_new_identifiers: generator %s', name)
                        self.assert_unknown(name, known, el.lineno)
                        add_here[name] = el.lineno
                        forget_here.add(name)
                del target, generators
            if hasattr(el, 'name'):
                if el.name is not None:
                    self.log.debug('check_new_identifiers: name %s', el.name)
                    self.assert_unknown(el.name, known, el.lineno)
                    add_here[el.name] = el.lineno
            self.log.debug('forget here: %s, %s, add here: %s %s ----', forget_here, forget - forget_here, set(add_here.keys()), add.keys() - add_here.keys())
            self.log.debug('checking access: %s', sorted(get_all_ids(el)))
            for name in get_all_ids(el):
                self.known_checked += 1
                if isinstance(getattr(el, 'ctx', None), ast.Del) or isinstance(el, ast.Delete):
                    self.log.debug('check_new_identifiers: check delete name %s', name)
                    if name in known or name in add or name in add_here:
                        pass
                    elif isinstance(node, ast.Try) and any(isinstance(handler.type, ast.Name) and handler.type.id == 'NameError' for handler in node.handlers if isinstance(handler, ast.ExceptHandler)):
                        # this is in a construct for testing whether a variable exists
                        pass
                    else:
                        # self.log.debug('known: %s', sorted(known.keys()))
                        self.variable_unknown_found(el.lineno, name)
                else:
                    self.log.debug('check_new_identifiers: check name %s', name)
                    if name in known or name in add or name in add_here:
                        pass
                    elif isinstance(node, ast.Try) and any(isinstance(handler.type, ast.Name) and handler.type.id == 'NameError' for handler in node.handlers if isinstance(handler, ast.ExceptHandler)):
                        # this is in a construct for testing whether a variable exists
                        pass
                    else:
                        # self.log.debug('known: %s', sorted(known.keys()))
                        self.variable_unknown_found(el.lineno, name)

            add.update(add_here)
            forget |= forget_here
            del forget_here, add_here

        for name, lineno in add.items():
            if name not in known:
                # print('+%s' % name)
                known[name] = lineno
        for name in forget:
            if name in known:
                # print('-%s' % name)
                del known[name]
        self.log.debug('known: %s', known.keys() - preknown)

    def walk_tree(self, nodes, preknown={}, depth=0):
        known_nodes = dict(**preknown)
        depthstr = ' ' * depth
        terminated = False
        for node in nodes:
            # print(); import pprintast; pprintast.pprintast(node)
            if isinstance(node, ast.Return):
                terminated |= True
                break
            if isinstance(node, ast.Expr) and isinstance(node.value, ast.Call) and isinstance(node.value.func, ast.Attribute) and isinstance(node.value.func.value, ast.Name):
                if node.value.func.value.id == 'sys' and node.value.func.attr == 'exit':
                    terminated |= True
                    break
            self.log.debug(
                '%swalk tree: %s[args:%s, assigned:%s] (terminating: %d)', depthstr,
                type(node).__name__, set(get_arg_ids(node)), set(get_assigned_ids(node)), terminated)

            # modified = getattr(node, 'decorator_list', []) != []

            if not is_container(node):
                self.check_new_identifiers([node], node, dict(**known_nodes))
            elif hasattr(node, 'name'):
                self.log.debug('%s+node name: %s', depthstr, node.name)
                self.assert_unknown(node.name, known_nodes, node.lineno)
                known_nodes[node.name] = (True, node.lineno)

            if not isinstance(node, ast.AugAssign) and not isinstance(node, ast.Name):
                for name in get_assigned_ids(node):
                    self.log.debug('%s+node assigned name: %s', depthstr, name)
                    if isinstance(node, ast.Assign):
                        self.assert_unknown(name, known_nodes, node.lineno)
                    known_nodes[name] = (True, node.lineno)
            for name in get_deleted_ids(node):
                self.log.debug('%s+node deleted name: %s', depthstr, name)
                known_nodes[name] = (False, node.lineno)

            if hasattr(node, 'generators'):
                # ignore result, because variables do not leak out
                known_nodes2 = dict(**known_nodes)
                for g in node.generators[::-1]:
                    for name in get_assigned_ids(g):
                        self.log.debug('%s+generator %s name: %s', depthstr, g, name)
                        self.assert_unknown(name, known_nodes2, node.lineno)
                        known_nodes2[name] = (True, node.lineno)
                    self.walk_tree([g.target], known_nodes2, depth + 1)
            if hasattr(node, 'test'):
                # ignore result, because variables do not leak out
                self.check_new_identifiers([node.test], node, dict(**known_nodes))
            if hasattr(node, 'iter'):
                # ignore result, because variables do not leak out
                self.check_new_identifiers([node.iter], node, dict(**known_nodes))
            if hasattr(node, 'value'):
                # ignore result, because variables do not leak out
                self.walk_tree([node.value], dict(**known_nodes), depth + 1)
                # self.check_new_identifiers([node.value], node, dict(**known_nodes))
            # if hasattr(node, 'target'):
            #     for name in get_assigned_ids(node.target):
            #         self.log.debug('+node target %s', name)
            #         self.assert_unknown(name, known_nodes, node.lineno)
            #         known_nodes[name] = (True, node.lineno)

            nodes_to_add = {}
            nbranches = 0

            known_nodes2 = dict(**known_nodes)
            if hasattr(node, 'args') and isinstance(node.args, ast.arguments):
                self.log.debug('checking call args: %s', node.args)
                for name in get_arg_ids(node):
                    self.log.debug('checking call arg: %s', name)
                    self.assert_unknown(name, known_nodes2, node.lineno)
                    known_nodes2[name] = (True, node.lineno)
            else:
                for arg in getattr(node, 'args', []) + getattr(node, 'keywords', []):
                    for name in get_all_ids(arg):
                        if name not in known_nodes or not known_nodes[name][0]:
                            self.variable_unknown_found(node.lineno, name)
                        known_nodes2[name] = (True, node.lineno)
            if hasattr(node, 'body'):
                body = node.body if isinstance(node.body, list) else [node.body]
                members = self.walk_tree(body, known_nodes2, depth + 1)
                if not is_container(node) and not block_terminates(body):
                    nbranches += 1
                    for name, var in members.items():
                        if name not in known_nodes or known_nodes[name][0] != var[0]:
                            nodes_to_add[name] = (nodes_to_add.get(name, (0, None))[0] + 1, var)
                self.log.debug('%s+nodes from body: %s', depthstr, nodes_to_add)

            for handler in getattr(node, 'handlers', []):
                members = self.walk_tree(handler.body, known_nodes, depth + 1)
                if not block_terminates(handler.body):
                    nbranches += 1
                    known_nodes2 = dict(**known_nodes)
                    if handler.name is not None:
                        known_nodes2[handler.name] = (True, handler.lineno)
                        nodes_to_add[handler.name] = (nodes_to_add.get(handler.name, (0, None))[0] + 1, (True, handler.lineno))
                    for name, var in members.items():
                        if name not in known_nodes or known_nodes[name][0] != var[0]:
                            nodes_to_add[name] = (nodes_to_add.get(name, (0, None))[0] + 1, var)
                self.log.debug('%s+nodes from handlers: %s', depthstr, nodes_to_add)

            if getattr(node, 'orelse', None) is not None:
                self.log.debug('%s+nodes from else: %s', depthstr, node.orelse)
                members = self.walk_tree([node.orelse], known_nodes, depth + 1)
                if not block_terminates([node.orelse]):
                    nbranches += 1
                    for name, var in members.items():
                        if name not in known_nodes or known_nodes[name][0] != var[0]:
                            nodes_to_add[name] = (nodes_to_add.get(name, (0, None))[0] + 1, var)
                self.log.debug('%s+nodes from else: %s', depthstr, nodes_to_add)

            for name, (nbranches_adding, var) in nodes_to_add.items():
                if nbranches_adding == nbranches:
                    self.assert_unknown(name, known_nodes, node.lineno)
                    if not is_container(node):
                        self.log.debug('%s+%s (from all branches)', depthstr, name)
                        known_nodes[name] = True, var[1]
                else:
                    if not is_container(node):
                        known_nodes[name] = None, var[1]
                        self.log.debug('%s+%s (in some branches)', depthstr, name)

            if getattr(node, 'finalbody', []) != []:
                members = self.walk_tree(node.finalbody, known_nodes, depth + 1)
                if not block_terminates(node.finalbody):
                    for name, var in members.items():
                        if name not in known_nodes or known_nodes[name][0] != var[0]:
                            self.log.debug('%s+%s (from final)', depthstr, name)
                            known_nodes[name] = var
                self.log.debug('%s+nodes from final: %s', depthstr, members)

            self.log.debug('%scurrent knowledge: %s', depthstr, known_nodes.keys() - preknown.keys())

        return known_nodes


def main(filenames, module_load_policy='none', allow_variable_reuse=False):
    """Verify python files listed in filenames.

    :param filenames: files to analyse
    :param module_load_policy: passed to ModuleCallLister
    :param allow_variable_reuse: whether variable reuse should be a error or warning
    """
    known_functions = dict()
    FuncLister.load_builtin_functions()
    total_checked_calls = 0
    total_checked_known_var = 0
    total_checked_unknown_var = 0
    total_checked_docstrings = 0

    asts = []
    for filename in filenames:
        a = ast.parse(open(filename).read())

        print("%s: checking class usage ..." % filename)
        ClassPropertiesLister(filename=filename).visit(a)
        print("%s: checking internals usage ..." % filename)
        mcl = ModuleCallLister(filename=filename, load_policy=module_load_policy)
        mcl.visit(a)
        total_checked_calls += mcl.checked_calls

        funcs = FuncLister(filename=filename)
        funcs.visit(a)
        known_functions.update(funcs.known_functions)

        asts.append((filename, a))
        del filename, a

    for filename, a in asts:
        known = {k: (True, 'builtin') for k in preknown}

        print("%s: checking calls ..." % filename)
        cl = CallLister(filename=filename, known_functions=known_functions)
        cl.visit(a)
        total_checked_calls += cl.checked_calls

        print("%s: checking variables ..." % filename)
        nameassigner = NameAssignVerifier(filename, allow_variable_reuse=allow_variable_reuse)
        nameassigner.walk_tree(a.body, known)
        total_checked_known_var += nameassigner.known_checked
        total_checked_unknown_var += nameassigner.unknown_checked
        if nameassigner.found_variable_unknown:
            sys.exit(2)
        if nameassigner.found_variable_reused and not allow_variable_reuse:
            sys.exit(3)
        if nameassigner.found_builtin_overwritten:
            sys.exit(4)
        print("%s: checking docstrings ..." % filename)
        funcdocs = FuncDocVerifier(filename=filename)
        funcdocs.visit(a)
        total_checked_docstrings += funcdocs.checked_docstrings
        if funcdocs.undocumented_parameters_found:
            sys.exit(5)
        if funcdocs.undocumented_returns_found:
            sys.exit(6)
    print("Summary:")
    print("  - checked %d function calls. " % (total_checked_calls))
    print("  - checked definition of %d new and access of %d variables." % (
        total_checked_unknown_var, total_checked_known_var))
    print("  - checked %d docstrings." % total_checked_docstrings)
    print("pystrict3: OK")
