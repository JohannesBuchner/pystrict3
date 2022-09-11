from pystrict3lib.funcchecker import list_documented_parameters, strip_left_indent, max_documented_returns

def fetch_smalltable_rows(table_handle,
                          keys,
                          require_all_keys,
):
    """Fetches rows from a Smalltable.

    Retrieves rows pertaining to the given keys from the Table instance
    represented by table_handle.  String keys will be UTF-8 encoded.

    Args:
        table_handle: An open smalltable.Table instance.
        keys: A sequence of strings representing the key of each table
          row to fetch.  String keys will be UTF-8 encoded.
        require_all_keys: If True only rows with values set for all keys will be
          returned.

    Returns:
        A dict mapping keys to the corresponding table row data
        fetched. Each row is represented as a tuple of strings. For
        example:

        {b'Serak': ('Rigel VII', 'Preparer'),
         b'Zim': ('Irk', 'Invader'),
         b'Lrrr': ('Omicron Persei 8', 'Emperor')}

        Returned keys are always bytes.  If a key from the keys argument is
        missing from the dictionary, then that row was not found in the
        table (and require_all_keys must have been False).

    Raises:
        IOError: An error occurred accessing the smalltable.

    Examples:
        Examples should be written in doctest format, and should illustrate how
        to use the function.

        >>> print([i for i in example_generator(4)])
        [0, 1, 2, 3]
    """
    pass
   
def foo(var1, var2, args, long_var_name='hi', *kwargs):
	r"""Summarize the function in one line.

	Several sentences providing an extended description. Refer to
	variables using back-ticks, e.g. `var`.

	Parameters
	----------
	var1 : array_like
		Array_like means all those objects -- lists, nested lists, etc. --
		that can be converted to an array.  We can also refer to
		variables like `var1`.
	var2 : int
		The type above can either refer to an actual Python type
		(e.g. ``int``), or describe the type of the variable in more
		detail, e.g. ``(N,) ndarray`` or ``array_like``.
	*args : iterable
		Other arguments.
	long_var_name : {'hi', 'ho'}, optional
		Choices in brackets, default first when optional.
	**kwargs : dict
		Keyword arguments.

	Returns
	-------
	type
		Explanation of anonymous return value of type ``type``.
	describe : type
		Explanation of return value named `describe`.
	out : type
		Explanation of `out`.
	type_without_description

	Other Parameters
	----------------
	only_seldom_used_keywords : type
		Explanation.
	common_parameters_listed_above : type
		Explanation.

	Raises
	------
	BadException
		Because you shouldn't have done that.

	See Also
	--------
	numpy.array : Relationship (optional).
	numpy.ndarray : Relationship (optional), which could be fairly long, in
					which case the line wraps here.
	numpy.dot, numpy.linalg.norm, numpy.eye

	Notes
	-----
	Notes about the implementation algorithm (if needed).

	This can have multiple paragraphs.

	You may include some math:

	.. math:: X(e^{j\omega } ) = x(n)e^{ - j\omega n}

	And even use a Greek symbol like :math:`\omega` inline.

	References
	----------
	Cite the relevant literature, e.g. [1]_.  You may also cite these
	references in the notes section above.

	.. [1] O. McNoleg, "The integration of GIS, remote sensing,
	   expert systems and adaptive co-kriging for environmental habitat
	   modelling of the Highland Haggis using object-oriented, fuzzy-logic
	   and neural-network techniques," Computers & Geosciences, vol. 22,
	   pp. 585-588, 1996.

	Examples
	--------
	These are written in doctest format, and should illustrate how to
	use the function.

	>>> a = [1, 2, 3]
	>>> print([x + 3 for x in a])
	[4, 5, 6]
	>>> print("a\nb")
	a
	b
	"""
	# After closing class docstring, there should be one blank line to
	# separate following codes (according to PEP257).
	# But for function, method and module, there should be no blank lines
	# after closing the docstring.
	if True:
		return False, 'foo', list_documented_parameters('out'), [3,4]
	else:
		mylist = True, 'foo', 1, 2
		return mylist

def add(num1, num2):
    """
    Add up two integer numbers.

    This function simply wraps the ``+`` operator, and does not
    do anything interesting, except for illustrating what
    the docstring of a very simple function looks like.

    Parameters
    ----------
    num1 : int
        First number to add.
    num2 : int
        Second number to add.

    Returns
    -------
    int
        The sum of ``num1`` and ``num2``.

    See Also
    --------
    subtract : Subtract one integer from another.

    Examples
    --------
    >>> add(2, 2)
    4
    >>> add(25, 0)
    25
    >>> add(10, -10)
    0
    """
    return num1 + num2

def test_lstrip():

	assert strip_left_indent("""
    hello

    world
    """) == """
hello

world
"""

	assert strip_left_indent("""
	hello
	
	world
	""") == """
hello

world
"""

def get_extended_auxiliary_problem(loglike, transform, ctr, invcov, enlargement_factor, df=1):
    """Return a new loglike and transform based on an auxiliary distribution.

    Given a likelihood and prior transform, and information about
    the (expected) posterior peak, generates a auxiliary
    likelihood and prior transform that is identical but
    requires fewer nested sampling iterations.

    This is achieved by deforming the prior space, and undoing that
    transformation by correction weights in the likelihood.

    The auxiliary distribution used for transformation/weighting is
    a d-dimensional Student-t distribution.

    Parameters
    ------------
    loglike: function
        original likelihood function
    transform: function
        original prior transform function
    ctr: array
        Posterior center (in u-space).
    invcov: array
        Covariance of the posterior (in u-space).
    enlargement_factor: float
        Factor by which the scale of the auxiliary distribution is enlarged
        in all dimensions.

        For Gaussian-like posteriors, sqrt(ndim) seems to work,
        Heavier tailed or non-elliptical distributions may need larger factors.
    df: float
        Number of degrees of freedom of the auxiliary student-t distribution.
        The default is recommended. For truly gaussian posteriors,
        the student-t can be made more gaussian (by df>=30) for accelation.

    Returns
    ---------
    aux_loglike: function
        auxiliary loglikelihood function. Takes d + 1 parameters (see below).
        The likelihood is the same as loglike, but adds weights.
    aux_transform: function
        auxiliary transform function.
        Takes d u-space coordinates, and returns d + 1 p-space parameters.
        The first d return coordinates are identical to what ``transform`` would return.
        The final coordinate is the correction weight.
    """
    pass
	
def test_docstring_params():
	p1 = list_documented_parameters(fetch_smalltable_rows.__doc__)
	print(p1)
	assert p1 == ['table_handle', 'keys', 'require_all_keys']
	p2 = list_documented_parameters(foo.__doc__)
	print(p2)
	assert p2 == ['var1', 'var2', '*args', 'long_var_name', '**kwargs', 'only_seldom_used_keywords', 'common_parameters_listed_above']
	p3 = list_documented_parameters(add.__doc__)
	print(p3)
	assert p3 == ['num1', 'num2']
	assert list_documented_parameters("Oneliner") == []
	assert list_documented_parameters("\nArgs:\n") == []
	assert list_documented_parameters("\n:params foo:\n") == ['foo']


def test_docstring_returns():
	assert 1 == max_documented_returns(fetch_smalltable_rows.__doc__) or 1
	assert 4 == max_documented_returns(foo.__doc__) or 1
	assert 1 == max_documented_returns(add.__doc__) or 1
	assert 2 == max_documented_returns(get_extended_auxiliary_problem.__doc__)
