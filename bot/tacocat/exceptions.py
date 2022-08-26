"""exceptions.py

Defines custom exceptions for this project.
"""


class UnexpectedError(Exception):
    """
    An error that was flagged as possible by typing, etc. but I do not
    know what could cause it or its occurrence is not expected in the
    context it has been written.
    """


class InvariantError(Exception):
    """An error caused by inconsistency in invariants."""
