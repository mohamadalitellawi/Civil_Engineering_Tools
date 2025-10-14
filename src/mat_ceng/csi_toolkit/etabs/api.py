"""
ETABS API main class.

Provides high-level interface for ETABS operations.
"""

from typing import Optional
from loguru import logger

from ..core.base_api import BaseCSIAPI
from ..core.connection import CSISoftware
from ..core.exceptions import ModelError


class ETABSAPI(BaseCSIAPI):
    """
    Main API class for ETABS.
    
    Example:
        >>> from csi_toolkit.etabs import ETABSAPI
        >>> 
        >>> # Connect to new instance
        >>> with ETABSAPI() as etabs:
        >>>     etabs.connect(visible=True)
        >>>     etabs.create_blank_model()
        >>>     # Do work...
        >>>     etabs.save_model("my_model.edb")
    """
    
    def __init__(self, installation_path: Optional[str] = None):
        """
        Initialize ETABS API.
        
        Args:
            installation_path: Custom ETABS installation path
        """
        super().__init__(CSISoftware.ETABS, installation_path)
        logger.info("ETABS API initialized")
    
    def create_blank_model(self) -> None:
        """Create a new blank ETABS model."""
        if not self.is_connected:
            raise ModelError("Not connected to ETABS")
        
        try:
            self.model.InitializeNewModel()
            logger.info("Created blank ETABS model")
        except Exception as e:
            raise ModelError(f"Failed to create blank model: {str(e)}")
    
    def create_template_model(
        self,
        template_type: str = "BeamSlab",
        num_stories: int = 3,
        story_height: float = 3.0,
        num_bays_x: int = 3,
        bay_width_x: float = 6.0,
        num_bays_y: int = 3,
        bay_width_y: float = 6.0
    ) -> None:
        """
        Create a model from template.
        
        Args:
            template_type: Type of template (e.g., "BeamSlab", "FlatPlate")
            num_stories: Number of stories
            story_height: Height of each story (in current units)
            num_bays_x: Number of bays in X direction
            bay_width_x: Width of bays in X direction
            num_bays_y: Number of bays in Y direction
            bay_width_y: Width of bays in Y direction
        """
        if not self.is_connected:
            raise ModelError("Not connected to ETABS")
        
        try:
            # Initialize new model with template
            ret = self.model.File.NewGridOnly(
                num_bays_x,
                bay_width_x,
                num_bays_y,
                bay_width_y,
                num_stories,
                story_height
            )
            
            if ret == 0:
                logger.info(
                    f"Created template model: {num_stories} stories, "
                    f"{num_bays_x}x{num_bays_y} bays"
                )
            else:
                raise ModelError("Template creation failed")
                
        except Exception as e:
            raise ModelError(f"Failed to create template model: {str(e)}")
    
    def get_element_count(self) -> dict[str, int]:
        """
        Get count of elements in the ETABS model.
        
        Returns:
            Dictionary with element counts
        """
        if not self.is_connected:
            raise ModelError("Not connected to ETABS")
        
        try:
            counts = {}
            
            # Get number of points
            ret = self.model.PointObj.Count()
            counts['points'] = ret
            
            # Get number of frame elements
            ret = self.model.FrameObj.Count()
            counts['frames'] = ret
            
            # Get number of area elements
            ret = self.model.AreaObj.Count()
            counts['areas'] = ret
            
            # Get number of stories
            ret = self.model.Story.GetStories()
            counts['stories'] = ret[0]
            
            logger.debug(f"Element counts: {counts}")
            return counts
            
        except Exception as e:
            raise ModelError(f"Failed to get element count: {str(e)}")
    
    def get_project_info(self) -> dict[str, str]:
        """
        Get project information.
        
        Returns:
            Dictionary with project info
        """
        if not self.is_connected:
            raise ModelError("Not connected to ETABS")
        
        try:
            info = {}
            
            # Get project info items
            ret = self.model.GetProjectInfo()
            
            # ret format: (NumberItems, Item, Data)
            if ret[0] > 0:
                for i in range(ret[0]):
                    info[ret[1][i]] = ret[2][i]
            
            logger.debug(f"Project info retrieved: {len(info)} items")
            return info
            
        except Exception as e:
            raise ModelError(f"Failed to get project info: {str(e)}")
    
    def set_project_info(self, item: str, data: str) -> None:
        """
        Set project information item.
        
        Args:
            item: Info item name (e.g., "Company Name", "Engineer")
            data: Info value
        """
        if not self.is_connected:
            raise ModelError("Not connected to ETABS")
        
        try:
            ret = self.model.SetProjectInfo(item, data)
            if ret == 0:
                logger.info(f"Set project info: {item} = {data}")
            else:
                raise ModelError(f"Failed to set project info: {item}")
                
        except Exception as e:
            raise ModelError(f"Error setting project info: {str(e)}")