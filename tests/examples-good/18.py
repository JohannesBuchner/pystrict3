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
   
def foo(var1, var2, *args, long_var_name='hi', **kwargs):
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
	pass

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
