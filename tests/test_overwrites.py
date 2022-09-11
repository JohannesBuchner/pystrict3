import ast
from hypothesis import given
from hypothesis.strategies import text

from pystrict3lib import assert_unknown, preknown

def test_assert_unknown():
	node = ast.parse("print('hello world')").body[0]
	known = {}
	assert_unknown("name", known, node, "filename")

def test_assert_known():
	node = ast.parse("print('hello world')").body[0]
	known = {}
	assert_unknown("name", known, node, "filename")
