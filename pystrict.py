import ast
import sys
import keyword
import builtins
import pprintast

known_functions = dict()

class FuncLister(ast.NodeVisitor):
    def visit_FunctionDef(self, node):
        min_args = 0
        max_args = -1
        arguments = node.args
        if node.decorator_list == []:
            min_args = 0
            max_args = 0
            optional_args_start = len(arguments.args) - len(arguments.defaults)
            for i, arg in enumerate(arguments.args):
                max_args += 1
                if arguments.vararg and arg.arg in [arg2.arg for arg2 in arguments.vararg]:
                    pass
                elif arguments.kw_defaults and arg.arg in [arg2.arg for arg2 in arguments.kw_defaults]:
                    pass
                elif i < optional_args_start:
                    min_args += 1
        
        print('defined function "%s" with %d..%d arguments' % (node.name, min_args, max_args))
        known_functions[node.name] = (min_args, max_args)
        self.generic_visit(node)

class CallLister(ast.NodeVisitor):
    def visit_Call(self, node):
        self.generic_visit(node)
        if isinstance(node.func, ast.Attribute):
            return
        
        #pprintast.pprintast(node)
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
            start = max(0, node.lineno - 3)
            end = node.lineno + 2
            sys.stderr.write('WARNING: Function "%s" (%d..%d arguments) called with %d arguments near line %d of %s\n' % (funcname, min_args, max_args, nargs, node.lineno, filename))
            sys.stderr.write(''.join(open(sys.argv[1]).readlines()[start:end]))
            sys.stderr.write("\n")
        else:
            print("call(%s with %d args): OK" % (funcname, nargs))


def flat_walk(node):
    #print(node)
    yield node
    if not isinstance(node, ast.FunctionDef) and not isinstance(node, ast.ClassDef):
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
        sys.stderr.write('WARNING: Variable reuse: "%s" near line %d of %s\n' % (name, node.lineno, filename))
        sys.stderr.write(''.join(open(filename).readlines()[start:end]))
        sys.stderr.write("Known variables here: %s\n" % (known - set(builtins.__dict__)))
        sys.stderr.write("\n")

asts = []
for filename in sys.argv[1:]:
    a = ast.parse(open(filename).read())

    FuncLister().visit(a)
    asts.append((filename, a))

for filename, a in asts:
    known = set(builtins.__dict__)

    CallLister().visit(a)
    
    for node in a.body:
        #print()
        #print(node)
        #pprintast.pprintast(node)
        #print(known - set(builtins.__dict__))
        #print(''.join(open(sys.argv[1]).readlines()[node.lineno-3:node.lineno+2]))
        add_here = set()
        for el in flat_walk(node):
            #print(el, list(get_ids(getattr(el, 'target', None))), [n.asname or n.name for n in getattr(el, 'names', [])], [list(get_ids(t)) for t in getattr(el, 'targets', [])], [list(get_ids(t)) for t in getattr(el, 'generators', [])])
            # find all name nodes and look at ids
            if hasattr(el, 'names'):
                names = el.names
                for name in names:
                    if getattr(name, 'asname') is not None:
                        name = getattr(name, 'asname')
                    else:
                        name = name.name
                    #print("+%s" % name)
                    assert_unknown(name, node, filename)
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
                    else:
                        assert id in known or add_here, (el.lineno, id, known - set(builtins.__dict__), el)

        for id in add_here:
            if id not in known:
                print('+"%s"' % id)
                known.add(id)


