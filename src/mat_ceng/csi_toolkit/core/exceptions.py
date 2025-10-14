"""
Custom exceptions for CSI Toolkit.

This module defines all custom exceptions used throughout the CSI API toolkit.
"""


class CSIToolkitError(Exception):
    """Base exception for all CSI Toolkit errors."""
    pass


class ConnectionError(CSIToolkitError):
    """Raised when connection to CSI software fails."""
    pass


class APIInitializationError(CSIToolkitError):
    """Raised when API initialization fails."""
    pass


class ModelError(CSIToolkitError):
    """Raised when model operations fail."""
    pass


class ElementError(CSIToolkitError):
    """Raised when element operations fail."""
    pass


class LoadError(CSIToolkitError):
    """Raised when load operations fail."""
    pass


class ResultsError(CSIToolkitError):
    """Raised when extracting results fails."""
    pass


class ValidationError(CSIToolkitError):
    """Raised when input validation fails."""
    pass


class SoftwareNotFoundError(CSIToolkitError):
    """Raised when CSI software is not installed or found."""
    pass


class FileOperationError(CSIToolkitError):
    """Raised when file operations fail."""
    pass