"""exceptions.py

Defines custom exceptions for this project.

TODO: maybe ditch this system altogether and use builtin exceptions.
"""


class UnexpectedError(Exception):
    """
    An error that was flagged as possible by type hints, etc. but I do
    not know what could cause it or its occurrence is not expected in
    the context it has been written.
    """


class InvariantError(Exception):
    """
    An error caused by a violation of invariants. Invariants include
    function preconditions, postconditions, constraints on argument
    types or values, etc.
    """


class NotFoundError(Exception):
    """Generic error when a certain resource cannot be found."""


class NotApplicableError(Exception):
    """Generic error when something is not applicable."""
