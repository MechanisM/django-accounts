"""
Module that lets you do fancy things with breakpoints.
"""
import pdb
named_bp = {}

def set(name="default"):
    named_bp[name] = True
    
def trace(name="default"):
    if named_bp.get(name):
        del named_bp[name]
        return pdb.set_trace
    else:
        return lambda: False
    