class HoneybadgerbftError(Exception):
    """Base exception class."""


class BroadcastError(HoneybadgerbftError):
    """Base class for broadcast errors."""



class UnknownTagError(BroadcastError):
    """Raised when an unknown broadcast tag is detected."""


class RedundantMessageError(BroadcastError):
    """Raised when a rdundant message is received."""

class CommonCoinFailureException(Exception):
    """Raised for common coin failures."""
    

class AbandonedNodeError(HoneybadgerbftError):
    """Raised when a node does not have enough peer to carry on a distirbuted task."""


class InvalidArgsError(HoneybadgerbftError):
    """Raised when binaryagreement receive a invalid input"""


class WrongTypeError(HoneybadgerbftError):
    """Raised when RBC receive wrong type input"""
    
    
