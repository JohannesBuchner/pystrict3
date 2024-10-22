
class Foo(object):
    def __init__(self, a, b):
        """Initialise.

    Parameters
    -----------
    a: int
        a friendly number
    b: str
        a friendly string
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

def bar(a: float, b, c=False):
    """<summary sentence of function in imperative>.
    
    
    Parameters
    -----------
    a: float
        a friendly number
    b: str
        a friendly string
    c: bool
        <MEANING OF c>
    
    Returns
    ----------
    <NAME>: <TYPE>
        <MEANING OF <NAME>>
    """
    return a + b


