__version__ = "2.0.1"

from .dea_check import \
    calc_model

def test(*args, **kwargs):
    '''
    Run py.test unit tests.
    '''
    import testr
    return testr.test(*args, **kwargs)
