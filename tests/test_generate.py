import ast
from hypothesis import given
from hypothesis.strategies import text

from pystrict3lib import preknown

def make_constant():
	value = rng.choice([
		123,
		'foo',
		None
	])
	return ast.Constant(value=value, kind=rng.choice(['u', None]))
	
def make_list(rng, ctx):
	return ast.List(make_nodes_list(rng), ctx=ctx)

def make_tuple(rng, ctx):
	return ast.Tuple(make_nodes_list(rng), ctx=ctx)

def make_set(rng, ctx):
	return ast.Tuple(make_nodes_list(rng), ctx=ctx)

def make_dict(rng, ctx):
	keys = make_nodes_list(rng)
	values = make_nodes_list(rng)
	N = min(len(keys), len(values))
	keys, values = keys[:N], values[:N]
	if N > 0 and rng.random() < 0.04:
		i = rng.randint(0, N-1)
		keys.insert(i, None)
		values.insert(i, make_expression(rng))
	return ast.Dict()

def make_literal(rng, ctx):
	return rng.choice([
		make_constant(),
		make_list(rng, ctx=ctx),
		make_tuple(rng, ctx=ctx),
		make_set(rng, ctx=ctx),
		make_dict(rng, ctx=ctx),
	])

def make_variable(rng, ctx):
	if rng.uniform() < 0.1:
		return ast.Starred(value=make_variable(rng, ctx))
	else:
		return ast.Name(id='v%d' % rng.randint(10), ctx=ctx)

def make_expression(rng, ctx):
	ast.Expr(rng.choice([
		make_op(rng),
		ast.Name(id='v%d' % rng.randint(10), ctx=ctx),
	]))

def test_generate():
	
