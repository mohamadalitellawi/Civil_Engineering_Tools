"""
Connection manager for CSI software applications.

Handles connecting to existing instances or starting new processes.
"""

import clr
import sys
from pathlib import Path
from typing import Optional, Any
from enum import Enum
from loguru import logger

from .exceptions import ConnectionError, SoftwareNotFoundError, APIInitializationError


class CSISoftware(Enum):
    """Enumeration of supported CSI software."""
    ETABS = "ETABS"
    SAP2000 = "SAP2000"
    SAFE = "SAFE"


class ConnectionManager:
    """
    Manages connections to CSI software applications.
    
    This class handles both attaching to existing instances and creating new ones.
    """
    
    # Default installation paths for different CSI software
    DEFAULT_PATHS = {
        CSISoftware.ETABS: r"C:\Program Files\Computers and Structures\ETABS 22",
        CSISoftware.SAP2000: r"C:\Program Files\Computers and Structures\SAP2000 26",
        CSISoftware.SAFE: r"C:\Program Files\Computers and Structures\SAFE 22",
    }
    
    # API DLL names
    API_DLLS = {
        CSISoftware.ETABS: "ETABSv1.dll",
        CSISoftware.SAP2000: "SAP2000v1.dll",
        CSISoftware.SAFE: "SAFEv1.dll",
    }
    
    def __init__(self, software: CSISoftware, installation_path: Optional[str] = None):
        """
        Initialize connection manager.
        
        Args:
            software: Type of CSI software
            installation_path: Custom installation path. If None, uses default.
        """
        self.software = software
        self.installation_path = Path(installation_path) if installation_path else Path(
            self.DEFAULT_PATHS[software]
        )
        self.api_dll_path = self.installation_path / self.API_DLLS[software]
        self.sap_object = None
        self.sap_model = None
        
        logger.info(f"Initializing ConnectionManager for {software.value}")
        self._verify_installation()
    
    def _verify_installation(self) -> None:
        """Verify that the software is installed at the specified path."""
        if not self.installation_path.exists():
            raise SoftwareNotFoundError(
                f"{self.software.value} not found at {self.installation_path}. "
                f"Please verify installation or provide correct path."
            )
        
        if not self.api_dll_path.exists():
            raise SoftwareNotFoundError(
                f"API DLL not found: {self.api_dll_path}. "
                f"Please verify {self.software.value} installation."
            )
        
        logger.debug(f"Verified installation at {self.installation_path}")
    
    def _load_api_dll(self) -> None:
        """Load the API DLL into Python.NET."""
        try:
            # Add installation path to system path
            sys.path.append(str(self.installation_path))
            
            # Load the DLL
            clr.AddReference(str(self.api_dll_path))
            logger.info(f"Loaded API DLL: {self.api_dll_path}")
        except Exception as e:
            raise APIInitializationError(
                f"Failed to load API DLL {self.api_dll_path}: {str(e)}"
            )
    
    def attach_to_instance(self) -> tuple[Any, Any]:
        """
        Attach to an existing running instance of the software.
        
        Returns:
            Tuple of (SapObject, SapModel)
        
        Raises:
            ConnectionError: If attachment fails
        """
        try:
            logger.info(f"Attempting to attach to existing {self.software.value} instance...")
            self._load_api_dll()
            
            # Import the appropriate module
            if self.software == CSISoftware.ETABS:
                import ETABSv1
                helper = ETABSv1.Helper()
            elif self.software == CSISoftware.SAP2000:
                import SAP2000v1
                helper = SAP2000v1.Helper()
            else:  # SAFE
                import SAFEv1
                helper = SAFEv1.Helper()
            
            # Attach to existing instance
            try:
                self.sap_object = helper.GetObject("CSI.ETABS.API.ETABSObject")
            except:
                # Try without specific object type
                self.sap_object = helper.GetObject("")
            
            # Get the model
            self.sap_model = self.sap_object.SapModel
            
            logger.info(f"Successfully attached to {self.software.value}")
            return self.sap_object, self.sap_model
            
        except Exception as e:
            raise ConnectionError(
                f"Failed to attach to {self.software.value}: {str(e)}"
            )
    
    def create_new_instance(
        self,
        visible: bool = True,
        model_path: Optional[str] = None
    ) -> tuple[Any, Any]:
        """
        Create a new instance of the software.
        
        Args:
            visible: Whether to show the software GUI
            model_path: Path to model file to open. If None, creates blank model.
        
        Returns:
            Tuple of (SapObject, SapModel)
        
        Raises:
            ConnectionError: If instance creation fails
        """
        try:
            logger.info(f"Creating new {self.software.value} instance...")
            self._load_api_dll()
            
            # Import the appropriate module
            if self.software == CSISoftware.ETABS:
                import ETABSv1
                helper = ETABSv1.Helper()
                self.sap_object = helper.CreateObjectProgID("CSI.ETABS.API.ETABSObject")
            elif self.software == CSISoftware.SAP2000:
                import SAP2000v1
                helper = SAP2000v1.Helper()
                self.sap_object = helper.CreateObjectProgID("CSI.SAP2000.API.SapObject")
            else:  # SAFE
                import SAFEv1
                helper = SAFEv1.Helper()
                self.sap_object = helper.CreateObjectProgID("CSI.SAFE.API.SAFEObject")
            
            # Start application
            self.sap_object.ApplicationStart()
            
            # Get the model
            self.sap_model = self.sap_object.SapModel
            
            # Initialize model
            if model_path:
                ret = self.sap_model.File.OpenFile(model_path)
                if ret != 0:
                    raise ConnectionError(f"Failed to open model file: {model_path}")
                logger.info(f"Opened model: {model_path}")
            else:
                self.sap_model.InitializeNewModel()
                logger.info("Initialized blank model")
            
            # Set visibility
            if visible:
                self.sap_object.Visible = True
            
            logger.info(f"Successfully created {self.software.value} instance")
            return self.sap_object, self.sap_model
            
        except Exception as e:
            raise ConnectionError(
                f"Failed to create {self.software.value} instance: {str(e)}"
            )
    
    def disconnect(self) -> None:
        """Disconnect from the software and cleanup."""
        try:
            if self.sap_object:
                logger.info(f"Disconnecting from {self.software.value}...")
                self.sap_object = None
                self.sap_model = None
                logger.info("Disconnected successfully")
        except Exception as e:
            logger.error(f"Error during disconnect: {str(e)}")