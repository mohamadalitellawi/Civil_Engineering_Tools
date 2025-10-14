"""
CSI Toolkit - Professional Python library for CSI software integration.

Provides high-level APIs for ETABS, SAP2000, and SAFE.
"""

__version__ = "0.1.0"
__author__ = "Your Name"
__email__ = "your.email@example.com"

from .utils.logging_config import setup_logging

# Expose main APIs
from .etabs.api import ETABSAPI

__all__ = [
    "ETABSAPI",
    "setup_logging",
]