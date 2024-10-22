
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
        return 42

def bar(a: float, b, c=False):
    return a + b


