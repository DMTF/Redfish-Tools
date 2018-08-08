from .discrepancy_list import DiscrepancyList

def pytest_assertrepr_compare(op, left, right):
    """ Helper to let us report on a list of things that went wrong. """
    if op == '==' and left == [] and isinstance(right, DiscrepancyList):
        right.insert(0, 'no discrepancies:')
        return right
