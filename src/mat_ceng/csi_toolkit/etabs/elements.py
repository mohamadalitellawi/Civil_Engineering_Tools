"""
ETABS elements manipulation module.

Handles creation and modification of structural elements (frames, areas, points, etc.).
"""

from typing import Optional, List, Tuple
from loguru import logger
import pandas as pd

from ..core.exceptions import ElementError


class ETABSElements:
    """
    Handler for ETABS structural elements.
    
    This class provides methods to create, modify, and query structural elements.
    """
    
    def __init__(self, model):
        """
        Initialize elements handler.
        
        Args:
            model: ETABS SapModel object
        """
        self.model = model
        logger.info("ETABS Elements handler initialized")
    
    # ==================== POINT OBJECTS ====================
    
    def add_point(
        self,
        x: float,
        y: float,
        z: float,
        name: Optional[str] = None,
        merge_tolerance: float = 0.001
    ) -> str:
        """
        Add a point object to the model.
        
        Args:
            x, y, z: Coordinates of the point
            name: Optional name for the point
            merge_tolerance: Distance within which points are merged
        
        Returns:
            Name of the created point
        """
        try:
            if name:
                ret = self.model.PointObj.AddCartesian(x, y, z, name, name)
            else:
                ret = self.model.PointObj.AddCartesian(x, y, z)
            
            point_name = ret[0]
            logger.info(f"Added point: {point_name} at ({x}, {y}, {z})")
            return point_name
            
        except Exception as e:
            raise ElementError(f"Failed to add point: {str(e)}")
    
    def get_all_points(self) -> pd.DataFrame:
        """
        Get all points in the model.
        
        Returns:
            DataFrame with point names and coordinates
        """
        try:
            ret = self.model.PointObj.GetNameList()
            
            if ret[0] == 0:
                logger.warning("No points found in model")
                return pd.DataFrame(columns=['Name', 'X', 'Y', 'Z'])
            
            point_names = ret[1]
            data = []
            
            for name in point_names:
                coords = self.model.PointObj.GetCoordCartesian(name)
                data.append({
                    'Name': name,
                    'X': coords[0],
                    'Y': coords[1],
                    'Z': coords[2]
                })
            
            df = pd.DataFrame(data)
            logger.debug(f"Retrieved {len(df)} points")
            return df
            
        except Exception as e:
            raise ElementError(f"Failed to get points: {str(e)}")
    
    # ==================== FRAME OBJECTS ====================
    
    def add_frame(
        self,
        point1: str,
        point2: str,
        section: str = "FSEC1",
        name: Optional[str] = None
    ) -> str:
        """
        Add a frame element between two points.
        
        Args:
            point1: Name of first point
            point2: Name of second point
            section: Section property name
            name: Optional name for frame
        
        Returns:
            Name of created frame
        """
        try:
            if name:
                ret = self.model.FrameObj.AddByPoint(point1, point2, name, section, name)
            else:
                ret = self.model.FrameObj.AddByPoint(point1, point2, "", section)
            
            frame_name = ret[0]
            
            # Assign section property
            self.model.FrameObj.SetSection(frame_name, section)
            
            logger.info(f"Added frame: {frame_name} ({point1} to {point2})")
            return frame_name
            
        except Exception as e:
            raise ElementError(f"Failed to add frame: {str(e)}")
    
    def get_all_frames(self) -> pd.DataFrame:
        """
        Get all frame elements in the model.
        
        Returns:
            DataFrame with frame information
        """
        try:
            ret = self.model.FrameObj.GetNameList()
            
            if ret[0] == 0:
                logger.warning("No frames found in model")
                return pd.DataFrame(columns=['Name', 'Point1', 'Point2', 'Section'])
            
            frame_names = ret[1]
            data = []
            
            for name in frame_names:
                points = self.model.FrameObj.GetPoints(name)
                section = self.model.FrameObj.GetSection(name)
                
                data.append({
                    'Name': name,
                    'Point1': points[0],
                    'Point2': points[1],
                    'Section': section[0]
                })
            
            df = pd.DataFrame(data)
            logger.debug(f"Retrieved {len(df)} frames")
            return df
            
        except Exception as e:
            raise ElementError(f"Failed to get frames: {str(e)}")
    
    def set_frame_section(self, frame_name: str, section_name: str) -> None:
        """
        Set section property for a frame.
        
        Args:
            frame_name: Name of frame element
            section_name: Name of section property
        """
        try:
            ret = self.model.FrameObj.SetSection(frame_name, section_name)
            if ret == 0:
                logger.info(f"Set section '{section_name}' for frame '{frame_name}'")
            else:
                raise ElementError(f"Failed to set section for frame {frame_name}")
                
        except Exception as e:
            raise ElementError(f"Error setting frame section: {str(e)}")
    
    # ==================== AREA OBJECTS ====================
    
    def add_area_by_points(
        self,
        points: List[str],
        name: Optional[str] = None
    ) -> str:
        """
        Add an area object defined by corner points.
        
        Args:
            points: List of point names (3 or 4 points)
            name: Optional name for area
        
        Returns:
            Name of created area
        """
        try:
            num_points = len(points)
            if num_points < 3 or num_points > 4:
                raise ElementError("Area must have 3 or 4 corner points")
            
            point_array = tuple(points)
            
            if name:
                ret = self.model.AreaObj.AddByPoint(num_points, point_array, name, name)
            else:
                ret = self.model.AreaObj.AddByPoint(num_points, point_array)
            
            area_name = ret[0]
            logger.info(f"Added area: {area_name} with {num_points} points")
            return area_name
            
        except Exception as e:
            raise ElementError(f"Failed to add area: {str(e)}")
    
    def get_all_areas(self) -> pd.DataFrame:
        """
        Get all area elements in the model.
        
        Returns:
            DataFrame with area information
        """
        try:
            ret = self.model.AreaObj.GetNameList()
            
            if ret[0] == 0:
                logger.warning("No areas found in model")
                return pd.DataFrame(columns=['Name', 'NumPoints', 'Points'])
            
            area_names = ret[1]
            data = []
            
            for name in area_names:
                points = self.model.AreaObj.GetPoints(name)
                
                data.append({
                    'Name': name,
                    'NumPoints': points[0],
                    'Points': list(points[1])
                })
            
            df = pd.DataFrame(data)
            logger.debug(f"Retrieved {len(df)} areas")
            return df
            
        except Exception as e:
            raise ElementError(f"Failed to get areas: {str(e)}")
    
    # ==================== MATERIAL PROPERTIES ====================
    
    def add_material(
        self,
        name: str,
        material_type: int = 2,  # 2 = Concrete
        region: str = "ACI 318-14"
    ) -> None:
        """
        Add a material property.
        
        Args:
            name: Material name
            material_type: Material type (1=Steel, 2=Concrete, 3=NoDesign, etc.)
            region: Design code region
        """
        try:
            ret = self.model.PropMaterial.SetMaterial(name, material_type)
            if ret == 0:
                logger.info(f"Added material: {name} (type={material_type})")
            else:
                raise ElementError(f"Failed to add material {name}")
                
        except Exception as e:
            raise ElementError(f"Error adding material: {str(e)}")
    
    # ==================== SECTION PROPERTIES ====================
    
    def add_frame_section_rectangular(
        self,
        name: str,
        material: str,
        depth: float,
        width: float
    ) -> None:
        """
        Add a rectangular frame section.
        
        Args:
            name: Section name
            material: Material name
            depth: Section depth
            width: Section width
        """
        try:
            ret = self.model.PropFrame.SetRectangle(name, material, depth, width)
            if ret == 0:
                logger.info(
                    f"Added rectangular section: {name} "
                    f"({width}x{depth}, material={material})"
                )
            else:
                raise ElementError(f"Failed to add section {name}")
                
        except Exception as e:
            raise ElementError(f"Error adding frame section: {str(e)}")
    
    def add_slab_section(
        self,
        name: str,
        slab_type: int,  # 0=Shell-Thin, 1=Shell-Thick, 2=Plate, etc.
        material: str,
        thickness: float
    ) -> None:
        """
        Add a slab (area) section property.
        
        Args:
            name: Section name
            slab_type: Type of slab element
            material: Material name
            thickness: Slab thickness
        """
        try:
            ret = self.model.PropArea.SetSlab(name, slab_type, 0, material, thickness)
            if ret == 0:
                logger.info(
                    f"Added slab section: {name} "
                    f"(thickness={thickness}, material={material})"
                )
            else:
                raise ElementError(f"Failed to add slab section {name}")
                
        except Exception as e:
            raise ElementError(f"Error adding slab section: {str(e)}")