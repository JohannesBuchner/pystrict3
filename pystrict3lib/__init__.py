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
import builtins
import logging

from .funcchecker import FuncLister, FuncDocChecker, CallLister, ModuleCallLister
from .classchecker import ClassPropertiesLister

preknown = set(builtins.__dict__).union({'__doc__', '__file__', '__name__', '__annotations__', '__dict__', '__builtins__'})

"""
def flat_walk(node):
    yield node
    if not isinstance(node, ast.FunctionDef) and not isinstance(node, ast.AsyncFunctionDef) and not isinstance(node, ast.ClassDef) and not isinstance(node, ast.Lambda) \
            and not isinstance(node, ast.Import) and not isinstance(node, ast.ImportFrom):

        for child in ast.iter_child_nodes(node):
            yield from flat_walk(child)
"""

def get_arg_ids(node):
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
    if isinstance(node, ast.Name) and isinstance(node.ctx, ast.Del):
        yield node.id
    if hasattr(node, 'target'):
        yield from get_deleted_ids(node.target)
    if hasattr(node, 'targets'):
        for target in node.targets:
            yield from get_deleted_ids(target)

def is_container(node):
    return isinstance(node, ast.FunctionDef) or isinstance(node, ast.AsyncFunctionDef) or isinstance(node, ast.ClassDef) or isinstance(node, ast.Lambda) or isinstance(node, ast.Expr) or isinstance(node, ast.Call)


def get_all_ids(node):
    """get all ids defined in names, tuples and targets here"""
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
    for statement in statements:
        if isinstance(statement, ast.Return):
            return True
        if isinstance(statement, ast.Expr) and isinstance(statement.value, ast.Call) and isinstance(statement.value.func, ast.Attribute) and isinstance(statement.value.func.value, ast.Name):
            if statement.value.func.value.id == 'sys' and statement.value.func.attr == 'exit':
                return True
    return False

class NameAssignVerifier():
    def __init__(self, filename, allow_variable_reuse=False):
        self.filename = filename
        self.log = logging.getLogger('pystrict3.nameassign')
        self.found_variable_unknown = False
        self.found_variable_reused = False
        self.allow_variable_reuse = allow_variable_reuse
        self.found_builtin_overwritten = False

    def variable_unknown_found(self, lineno, id):
        sys.stderr.write('%s:%d: ERROR: Variable unknown: "%s"\n' % (self.filename, lineno, id))
        self.found_variable_unknown |= True
        raise Exception(id)

    def assert_unknown(self, name, known, lineno):
        """unified error message verifying `name` is in set `known`"""
        assert name is not None
        self.log.debug("assert_unknown: %s, %s", name, lineno)
        # the nested if allows deleting builtins and re-defining them afterwards
        if name in known:
            previous_state, previous_lineno = known[name]
            if name in preknown:
                sys.stderr.write('%s:%d: ERROR: Overwriting builtin variable: "%s"\n' % (
                    self.filename, lineno, name))
                self.found_builtin_overwritten |= True
                raise Exception(name)

            if name == '_':
                # throwaway variable is allowed
                pass
            elif previous_state is not None and previous_state == True:
                self.found_variable_reused |= True
                if self.allow_variable_reuse:
                    sys.stderr.write('%s:%d: ERROR: Variable "%s" set previously defined in line %d, is redefined here\n' % (
                        self.filename, lineno, name, known[name][1]))
                else:
                    sys.stderr.write('%s:%d: WARNING: Variable "%s" set previously in line %d may have changed meaning\n' % (
                        self.filename, lineno, name, known[name][1]))
                    raise Exception(name)


    def check_new_identifiers(self, elements, node, known):
        """add newly defined variables and verify that the accessed ones are defined in known"""
        #old_known = dict(**known)
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
                    self.assert_unknown(name, known, el.lineno)
                    name = name.split('.')[0]
                    add_here[name] = el.lineno
                del name, names
            if hasattr(el, 'targets'):
                targets = el.targets
                for target in targets:
                    self.log.debug('check_new_identifiers: target %s with ids: %s', target, set(get_assigned_ids(target)))
                    for id in get_assigned_ids(target):
                        if isinstance(getattr(target, 'ctx'), ast.Del):
                            self.log.debug('check_new_identifiers: del target id %s', id)
                            print("-%s" % id)
                            if id in add:
                                del add[id]
                            if id in add_here:
                                del add_here[id]
                            if id in known:
                                del known[id]
                            forget_here.add(id)
                        else:
                            self.log.debug('check_new_identifiers: add target id %s', id)
                            self.assert_unknown(id, known, el.lineno)
                            add_here[id] = el.lineno
                del target, targets
            if hasattr(el, 'items'):
                items = el.items
                for item in items:
                    self.log.debug('check_new_identifiers: item %s', item)
                    if item.optional_vars is None:
                        names = item.context_expr
                    else:
                        names = item.optional_vars
                    for id in get_all_ids(names):
                        self.assert_unknown(id, known, el.lineno)
                        add_here[id] = el.lineno
                    del names
                del item, items
            if hasattr(el, 'target') and not isinstance(el, ast.AugAssign):
                for id in get_assigned_ids(el.target):
                    self.log.debug('check_new_identifiers: target %s', id)
                    self.assert_unknown(id, known, el.lineno)
                    add_here[id] = node.lineno
            if hasattr(el, 'generators'):
                generators = el.generators
                for target in generators:
                    for id in get_assigned_ids(target):
                        self.log.debug('check_new_identifiers: generator %s', id)
                        self.assert_unknown(id, known, el.lineno)
                        add_here[id] = el.lineno
                        forget_here.add(id)
                del target, generators
            if hasattr(el, 'name'):
                if el.name is not None:
                    self.log.debug('check_new_identifiers: name %s', el.name)
                    self.assert_unknown(el.name, known, el.lineno)
                    add_here[el.name] = el.lineno
            self.log.debug('forget here: %s, %s, add here: %s %s ----', forget_here, forget - forget_here, set(add_here.keys()), add.keys() - add_here.keys())
            self.log.debug('checking access: %s', sorted(get_all_ids(el)))
            for id in get_all_ids(el):
                if isinstance(getattr(el, 'ctx', None), ast.Del) or isinstance(el, ast.Delete):
                    self.log.debug('check_new_identifiers: check delete id %s', id)
                    if id in known or id in add or id in add_here:
                        pass
                    elif isinstance(node, ast.Try) and any(isinstance(handler.type, ast.Name) and handler.type.id == 'NameError' for handler in node.handlers if isinstance(handler, ast.ExceptHandler)):
                        # this is in a construct for testing whether a variable exists
                        pass
                    else:
                        # self.log.debug('known: %s', sorted(known.keys()))
                        self.variable_unknown_found(el.lineno, id)
                else:
                    self.log.debug('check_new_identifiers: check id %s', id)
                    if id in known or id in add or id in add_here:
                        pass
                    elif isinstance(node, ast.Try) and any(isinstance(handler.type, ast.Name) and handler.type.id == 'NameError' for handler in node.handlers if isinstance(handler, ast.ExceptHandler)):
                        # this is in a construct for testing whether a variable exists
                        pass
                    else:
                        # self.log.debug('known: %s', sorted(known.keys()))
                        self.variable_unknown_found(el.lineno, id)

            add.update(add_here)
            forget |= forget_here
            del forget_here, add_here

        for id, lineno in add.items():
            if id not in known:
                print('+%s' % id)
                known[id] = lineno
        for id in forget:
            if id in known:
                print('-%s' % id)
                del known[id]
        self.log.debug('known: %s', known.keys() - preknown)


    def walk_tree(self, nodes, preknown={}, depth=0):
        known_nodes = dict(**preknown)
        terminated = False
        for node in nodes:
            #print(); import pprintast; pprintast.pprintast(node)
            if isinstance(node, ast.Return):
                terminated |= True
                break
            if isinstance(node, ast.Expr) and isinstance(node.value, ast.Call) and isinstance(node.value.func, ast.Attribute) and isinstance(node.value.func.value, ast.Name):
                if node.value.func.value.id == 'sys' and node.value.func.attr == 'exit':
                    terminated |= True
                    break
            self.log.debug('%swalk tree: %s[args:%s, assigned:%s] (terminating: %d)', '  '*depth, type(node).__name__, set(get_arg_ids(node)), set(get_assigned_ids(node)), terminated)

            # modified = getattr(node, 'decorator_list', []) != []
            
            if not is_container(node):
                self.check_new_identifiers([node], node, dict(**known_nodes))
            elif hasattr(node, 'name'):
                self.log.debug('%s+node name: %s', '  '*depth, node.name)
                self.assert_unknown(node.name, known_nodes, node.lineno)
                known_nodes[node.name] = (True, node.lineno)

            if not isinstance(node, ast.AugAssign) and not isinstance(node, ast.Name):
                for id in get_assigned_ids(node):
                    self.log.debug('%s+node assigned id: %s', '  '*depth, id)
                    if isinstance(node, ast.Assign):
                        self.assert_unknown(id, known_nodes, node.lineno)
                    known_nodes[id] = (True, node.lineno)
            for id in get_deleted_ids(node):
                self.log.debug('%s+node deleted id: %s', '  '*depth, id)
                known_nodes[id] = (False, node.lineno)
            
            if hasattr(node, 'generators'):
                # ignore result, because variables do not leak out
                known_nodes2 = dict(**known_nodes)
                for g in node.generators[::-1]:
                    for id in get_assigned_ids(g):
                        self.log.debug('%s+generator %s id: %s', '  '*depth, g, id)
                        self.assert_unknown(id, known_nodes2, node.lineno)
                        known_nodes2[id] = (True, node.lineno)
                    self.walk_tree([g.target], known_nodes2, depth+1)
            if hasattr(node, 'test'):
                # ignore result, because variables do not leak out
                self.check_new_identifiers([node.test], node, dict(**known_nodes))
            if hasattr(node, 'iter'):
                # ignore result, because variables do not leak out
                self.check_new_identifiers([node.iter], node, dict(**known_nodes))
            if hasattr(node, 'value'):
                # ignore result, because variables do not leak out
                self.walk_tree([node.value], dict(**known_nodes), depth+1)
                # self.check_new_identifiers([node.value], node, dict(**known_nodes))
            #if hasattr(node, 'target'):
            #    for id in get_assigned_ids(node.target):
            #        self.log.debug('+node target %s', id)
            #        self.assert_unknown(id, known_nodes, node.lineno)
            #        known_nodes[id] = (True, node.lineno)

            nodes_to_add = {}
            nbranches = 0

            known_nodes2 = dict(**known_nodes)
            if hasattr(node, 'args') and isinstance(node.args, ast.arguments):
                self.log.debug('checking call args: %s', node.args)
                for id in get_arg_ids(node):
                    self.log.debug('checking call arg: %s', id)
                    self.assert_unknown(id, known_nodes2, node.lineno)
                    known_nodes2[id] = (True, node.lineno)
            else:
                for arg in getattr(node, 'args', []) + getattr(node, 'keywords', []):
                    for id in get_all_ids(arg):
                        self.log.debug('checking call arg: %s', id)
                        if id not in known_nodes:
                            self.variable_unknown_found(node.lineno, id)
                        known_nodes2[id] = (True, node.lineno)
            if hasattr(node, 'body'):
                body = node.body if isinstance(node.body, list) else [node.body]
                members = self.walk_tree(body, known_nodes2, depth+1)
                if not is_container(node) and not block_terminates(body):
                    nbranches += 1
                    for id, var in members.items():
                        if id not in known_nodes or known_nodes[id][0] != var[0]:
                            nodes_to_add[id] = (nodes_to_add.get(id, (0, None))[0] + 1, var)
                self.log.debug('%s+nodes from body: %s', '  '*depth, nodes_to_add)

            for handler in getattr(node, 'handlers', []):
                members = self.walk_tree(handler.body, known_nodes, depth+1)
                if not block_terminates(handler.body):
                    nbranches += 1
                    known_nodes2 = dict(**known_nodes)
                    if handler.name is not None:
                        known_nodes2[handler.name] = (True, handler.lineno)
                        nodes_to_add[handler.name] = (nodes_to_add.get(handler.name, (0, None))[0] + 1, (True, handler.lineno))
                    for id, var in members.items():
                        if id not in known_nodes or known_nodes[id][0] != var[0]:
                            nodes_to_add[id] = (nodes_to_add.get(id, (0, None))[0] + 1, var)
                self.log.debug('%s+nodes from handlers: %s', '  '*depth, nodes_to_add)

            if getattr(node, 'orelse', []) != []:
                members = self.walk_tree(node.orelse, known_nodes, depth+1)
                if not block_terminates(node.orelse):
                    nbranches += 1
                    for id, var in members.items():
                        if id not in known_nodes or known_nodes[id][0] != var[0]:
                            nodes_to_add[id] = (nodes_to_add.get(id, (0, None))[0] + 1, var)
                self.log.debug('%s+nodes from else: %s', '  '*depth, nodes_to_add)

            for id, (nbranches_adding, var) in nodes_to_add.items():
                if nbranches_adding == nbranches:
                    self.assert_unknown(id, known_nodes, node.lineno)
                    if not is_container(node):
                        self.log.debug('%s+%s (from all branches)', '  '*depth, id)
                        known_nodes[id] = True, var[1]
                else:
                    if not is_container(node):
                        known_nodes[id] = None, var[1]
                        self.log.debug('%s+%s (in some branches)', '  '*depth, id)

            if getattr(node, 'finalbody', []) != []:
                members = self.walk_tree(node.finalbody, known_nodes, depth+1)
                if not block_terminates(node.finalbody):
                    for id, var in members.items():
                        if id not in known_nodes or known_nodes[id][0] != var[0]:
                            self.log.debug('%s+%s (from final)', '  '*depth, id)
                            known_nodes[id] = var
                self.log.debug('%s+nodes from final: %s', '  '*depth, members)
            
            self.log.debug('%scurrent knowledge: %s', '  '*depth, known_nodes.keys() - preknown.keys())

        return known_nodes


def main(filenames, module_load_policy='none', allow_variable_reuse=False):
    """ Verify python files listed in filenames """
    known_functions = dict()
    FuncLister.load_builtin_functions()
    logger = logging.getLogger('pystrict3.nameassign')
    handler = logging.StreamHandler(sys.stderr)
    handler.setLevel(logging.DEBUG)
    formatter = logging.Formatter('[%(levelname)s] %(message)s')
    handler.setFormatter(formatter)
    logger.addHandler(handler)
    logger.setLevel(logging.DEBUG)

    asts = []
    for filename in filenames:
        a = ast.parse(open(filename).read())

        print("%s: checking class usage ..." % filename)
        ClassPropertiesLister(filename=filename).visit(a)
        print("%s: checking internals usage ..." % filename)
        ModuleCallLister(filename=filename, load_policy=module_load_policy).visit(a)
        
        funcs = FuncLister(filename=filename)
        funcs.visit(a)
        known_functions.update(funcs.known_functions)
        
        asts.append((filename, a))

    for filename, a in asts:
        known = {k: (True, 'builtin') for k in preknown}

        print("%s: checking calls ..." % filename)
        CallLister(filename=filename, known_functions=known_functions).visit(a)
        
        print("%s: checking variables ..." % filename)
        nameassigner = NameAssignVerifier(filename, allow_variable_reuse=allow_variable_reuse)
        nameassigner.walk_tree(a.body, known)
        if nameassigner.found_variable_unknown:
            sys.exit(2)
        if nameassigner.found_variable_reused and not allow_variable_reuse:
            sys.exit(3)
        if nameassigner.found_builtin_overwritten:
            sys.exit(4)
        print("%s: checking docstrings ..." % filename)
        funcdocs = FuncDocChecker(filename=filename)
        funcdocs.visit(a)
        if funcdocs.undocumented_parameters_found:
            sys.exit(5)

    print("pystrict3: OK")
