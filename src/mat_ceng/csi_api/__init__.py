# src/csi_api/__init__.py

from .etabs.client import ETABSClient
#from .sap2000.client import SAP2000Client
#from .safe.client import SAFEClient
from .exceptions import CSIAPIError, ConnectionError, ModelError
from .core.exporter import export_to_csv  # Optional

__version__ = "0.2.0"