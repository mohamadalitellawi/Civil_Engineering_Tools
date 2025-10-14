"""
Base API class with common functionality for all CSI software.

This module provides the foundation for ETABS, SAP2000, and SAFE API classes.
"""

from abc import ABC, abstractmethod
from typing import Optional, Any
from loguru import logger

from .connection import ConnectionManager, CSISoftware
from .exceptions import ModelError


class BaseCSIAPI(ABC):
    """
    Abstract base class for CSI software APIs.
    
    Provides common functionality and interface for all CSI software types.
    """
    
    def __init__(
        self,
        software: CSISoftware,
        installation_path: Optional[str] = None
    ):
        """
        Initialize base API.
        
        Args:
            software: Type of CSI software
            installation_path: Custom installation path
        """
        self.software = software
        self.connection_manager = ConnectionManager(software, installation_path)
        self.sap_object: Optional[Any] = None
        self.model: Optional[Any] = None
        self.is_connected = False
        
        logger.info(f"Initialized {software.value} API")
    
    def connect(
        self,
        attach_to_existing: bool = False,
        visible: bool = True,
        model_path: Optional[str] = None
    ) -> None:
        """
        Connect to the software.
        
        Args:
            attach_to_existing: If True, attach to running instance. If False, create new.
            visible: Show GUI (only for new instances)
            model_path: Model file to open (only for new instances)
        """
        try:
            if attach_to_existing:
                self.sap_object, self.model = self.connection_manager.attach_to_instance()
            else:
                self.sap_object, self.model = self.connection_manager.create_new_instance(
                    visible=visible,
                    model_path=model_path
                )
            
            self.is_connected = True
            logger.info(f"Connected to {self.software.value}")
        except Exception as e:
            logger.error(f"Connection failed: {str(e)}")
            raise
    
    def disconnect(self) -> None:
        """Disconnect from the software."""
        if self.is_connected:
            self.connection_manager.disconnect()
            self.is_connected = False
    
    def __enter__(self):
        """Context manager entry."""
        return self
    
    def __exit__(self, exc_type, exc_val, exc_tb):
        """Context manager exit."""
        self.disconnect()
    
    def save_model(self, file_path: str) -> None:
        """
        Save the current model.
        
        Args:
            file_path: Path where to save the model
        """
        if not self.is_connected:
            raise ModelError("Not connected to software")
        
        try:
            ret = self.model.File.Save(file_path)
            if ret == 0:
                logger.info(f"Model saved: {file_path}")
            else:
                raise ModelError(f"Failed to save model to {file_path}")
        except Exception as e:
            raise ModelError(f"Error saving model: {str(e)}")
    
    def run_analysis(self) -> None:
        """Run the analysis."""
        if not self.is_connected:
            raise ModelError("Not connected to software")
        
        try:
            logger.info("Running analysis...")
            ret = self.model.Analyze.RunAnalysis()
            if ret == 0:
                logger.info("Analysis completed successfully")
            else:
                raise ModelError("Analysis failed")
        except Exception as e:
            raise ModelError(f"Error running analysis: {str(e)}")
    
    def unlock_model(self) -> None:
        """Unlock the model for editing."""
        if not self.is_connected:
            raise ModelError("Not connected to software")
        
        try:
            self.model.SetModelIsLocked(False)
            logger.debug("Model unlocked")
        except Exception as e:
            logger.error(f"Failed to unlock model: {str(e)}")
    
    def lock_model(self) -> None:
        """Lock the model to prevent editing."""
        if not self.is_connected:
            raise ModelError("Not connected to software")
        
        try:
            self.model.SetModelIsLocked(True)
            logger.debug("Model locked")
        except Exception as e:
            logger.error(f"Failed to lock model: {str(e)}")
    
    def refresh_view(self) -> None:
        """Refresh the software view."""
        if not self.is_connected:
            raise ModelError("Not connected to software")
        
        try:
            self.model.View.RefreshView()
            logger.debug("View refreshed")
        except Exception as e:
            logger.error(f"Failed to refresh view: {str(e)}")
    
    def get_model_units(self) -> tuple[int, int]:
        """
        Get current model units.
        
        Returns:
            Tuple of (force_units, length_units)
        """
        if not self.is_connected:
            raise ModelError("Not connected to software")
        
        try:
            ret = self.model.GetPresentUnits()
            return ret
        except Exception as e:
            raise ModelError(f"Failed to get units: {str(e)}")
    
    def set_model_units(self, force_unit: int, length_unit: int) -> None:
        """
        Set model units.
        
        Args:
            force_unit: Force unit code
            length_unit: Length unit code
        """
        if not self.is_connected:
            raise ModelError("Not connected to software")
        
        try:
            ret = self.model.SetPresentUnits(force_unit, length_unit)
            if ret == 0:
                logger.info(f"Units set: Force={force_unit}, Length={length_unit}")
            else:
                raise ModelError("Failed to set units")
        except Exception as e:
            raise ModelError(f"Error setting units: {str(e)}")
    
    @abstractmethod
    def get_element_count(self) -> dict[str, int]:
        """Get count of various elements in the model."""
        pass