import ast
import sys
import keyword
import builtins
import pprintast
import string

import pyparsing as pp

# from https://docs.python.org/3/library/stdtypes.html?highlight=string%20interpolation#printf-style-string-formatting
PCT,LPAREN,RPAREN,DOT = map(pp.Literal, '%().')
conversion_flag_expr = pp.oneOf(list("#0- +"))
conversion_type_expr = pp.oneOf(list("diouxXeEfFgGcrsa%"))
length_mod_expr = pp.oneOf(list("hlL"))
interp_expr = (
    PCT
    + pp.Optional(LPAREN + pp.Word(pp.printables, excludeChars=")")("mapping_key") + RPAREN)
    + pp.Optional(conversion_flag_expr("conversion_flag"))
    + pp.Optional(('*' | pp.pyparsing_common.integer)("min_width"))
    + pp.Optional(DOT + pp.pyparsing_common.integer("max_width"))
    + pp.Optional(length_mod_expr("length_modifier"))
    + conversion_type_expr("conversion_type")
)

strformatter = string.Formatter()

preknown = set(builtins.__dict__).union({'__doc__', '__file__', '__name__', '__annotations__', '__dict__ '})
known_functions = dict()

class StrFormatLister(ast.NodeVisitor):
    def visit_BinOp(self, node):
        if isinstance(node.op, ast.Mod) and isinstance(node.left, ast.Str) and isinstance(node.right, ast.Tuple):
            formatter = node.left.s
            nargs = len(node.right.elts)
            # this is for str.format():
            #nelements = strformatter.parse(formatter)
            nelements = list(interp_expr.scanString(formatter))
            #pprintast.pprintast(node)
            #print(formatter, len(nelements), nargs)
            if nargs != len(nelements):
                sys.stderr.write('%s:%d: ERROR: String interpolation "%s" (%d arguments) used with %d arguments\n' % (filename, node.lineno, formatter, len(nelements), nargs))
                sys.exit(1)
        #print('function "%s" has %d..%d arguments' % (node.name, min_args, max_args))
        self.generic_visit(node)

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
                elif arguments.kw_defaults and arg in [arg2.id for arg2 in arguments.kw_defaults]:
                    pass
                elif i < optional_args_start:
                    min_args += 1
            if arguments.vararg or arguments.kwarg:
                max_args = -1
        
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
            #start = max(0, node.lineno - 3)
            #end = node.lineno + 2
            sys.stderr.write('%s:%d: ERROR: Function "%s" (%d..%d arguments) called with %d arguments\n' % (filename, node.lineno, funcname, min_args, max_args, nargs))
            #sys.stderr.write(''.join(open(sys.argv[1]).readlines()[start:end]))
            #sys.stderr.write("\n")
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
        start = max(0, node.lineno - 2)
        end = node.lineno + 3
        sys.stderr.write('%s:%d: ERROR: Variable reuse: "%s"\n' % (filename, node.lineno, name))
        #sys.stderr.write(''.join(open(filename).readlines()[start:end]))
        #sys.stderr.write("Known variables here: %s\n" % (known - preknown))
        #sys.stderr.write("Built-ins: %s\n" % (set(builtins.__dict__)))
        #sys.stderr.write("\n")
        #raise Exception("Variable reuse")
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
                        #start = max(0, node.lineno - 2)
                        #end = node.lineno + 3
                        sys.stderr.write('%s:%d: ERROR: Variable unknown: "%s"\n' % (filename, node.lineno, id))
                        #sys.stderr.write('ERROR: Variable unknown: "%s" near line %d of %s\n' % (id, node.lineno, filename))
                        #sys.stderr.write(''.join(open(filename).readlines()[start:end]))
                        #sys.stderr.write("Known variables here: %s\n" % (known - set(preknown)))
                        #sys.stderr.write("\n")
                        sys.exit(1)
                        #assert id in known or add_here, (el.lineno, id, known - set(builtins.__dict__), el)
            
            for id in forget_here:
                if id in known:
                    print('-"%s"' % id)
                    known.remove(id)

        for id in add_here:
            if id not in known:
                print('+"%s"' % id)
                known.add(id)
        for id in forget_here:
            if id in known:
                print('-"%s"' % id)
                known.remove(id)



