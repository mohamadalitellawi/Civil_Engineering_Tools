# src/csi_api/exceptions.py

class CSIAPIError(Exception):
    """Base exception for CSI API errors."""
    pass

class ConnectionError(CSIAPIError):
    """Raised when connection to CSI software fails."""
    pass

class ModelError(CSIAPIError):
    """Raised when model operation fails."""
    pass
