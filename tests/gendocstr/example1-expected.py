
# some test functions:

def foo(a: float, b: int):
    """<summary sentence of function in imperative>.
    
    
    Parameters
    -----------
    a: float
        <MEANING OF a>
    b: int
        <MEANING OF b>
    """
    pass


def foo2(a: float, b: int):
    """<summary sentence of function in imperative>.
    
    
    Parameters
    -----------
    a: float
        <MEANING OF a>
    b: int
        <MEANING OF b>
    
    Returns
    ----------
    a: float
        <MEANING OF a>
    b: int
        <MEANING OF b>
    """
    if False:
        return a
    else:
        return b



def bar(a: int, b=3, c=False):
    """<summary sentence of function in imperative>.
    
    
    Parameters
    -----------
    a: int
        <MEANING OF a>
    b: int
        <MEANING OF b>
    c: bool
        <MEANING OF c>
    
    Returns
    ----------
    <NAME>: <TYPE>
        <MEANING OF <NAME>>
    """
    return a + b


def baz(a, b):
    """<summary sentence of function in imperative>.
    
    
    Parameters
    -----------
    a: <TYPE>
        <MEANING OF a>
    b: <TYPE>
        <MEANING OF b>
    
    Returns
    ----------
    a: <TYPE>
        <MEANING OF a>
    b: <TYPE>
        <MEANING OF b>
    <NAME>: <TYPE>
        <MEANING OF <NAME>>
    """
    return a, b, a + b, 3

def indicator(r):
    """<summary sentence of function in imperative>.
    
    
    Parameters
    -----------
    r: <TYPE>
        <MEANING OF r>
    
    Returns
    ----------
    indicator: bool
        <MEANING OF indicator>
    """
    if r > 42:
        return False
    else:
        return True


class Foo(object):
    def __init__(self, a: int, b=3):
        """<summary sentence of function in imperative>.
    
    
    Parameters
    -----------
    a: int
        <MEANING OF a>
    b: int
        <MEANING OF b>
    """
        pass
    def calc(self):
        """<summary sentence of function in imperative>.
    
    
    Returns
    ----------
    <NAME>: <TYPE>
        <MEANING OF <NAME>>
    """
        return 42
