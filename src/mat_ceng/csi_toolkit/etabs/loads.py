"""
ETABS loads module.

Handles creation and management of load patterns, load cases, and load assignments.
"""

from typing import Optional, List
from loguru import logger
import pandas as pd

from ..core.exceptions import LoadError


class ETABSLoads:
    """
    Handler for ETABS loads and load patterns.
    
    This class provides methods to define load patterns and apply loads to elements.
    """
    
    def __init__(self, model):
        """
        Initialize loads handler.
        
        Args:
            model: ETABS SapModel object
        """
        self.model = model
        logger.info("ETABS Loads handler initialized")
    
    # ==================== LOAD PATTERNS ====================
    
    def add_load_pattern(
        self,
        name: str,
        load_type: int,
        self_weight_multiplier: float = 0.0
    ) -> None:
        """
        Add a load pattern.
        
        Args:
            name: Load pattern name
            load_type: Type of load (1=Dead, 2=SuperDead, 3=Live, etc.)
            self_weight_multiplier: Multiplier for self-weight
        
        Load Types:
            1 = Dead
            2 = SuperDead
            3 = Live
            4 = Reducible Live
            5 = Earthquake
            6 = Wind
            7 = Snow
            8 = Other
            9 = Move
            10 = Temperature
            11 = Roof Live
            12 = Notional
            13 = Pattern Live
        """
        try:
            ret = self.model.LoadPatterns.Add(name, load_type, self_weight_multiplier)
            if ret == 0:
                logger.info(
                    f"Added load pattern: {name} "
                    f"(type={load_type}, SW mult={self_weight_multiplier})"
                )
            else:
                raise LoadError(f"Failed to add load pattern {name}")
                
        except Exception as e:
            raise LoadError(f"Error adding load pattern: {str(e)}")
    
    def get_all_load_patterns(self) -> pd.DataFrame:
        """
        Get all load patterns in the model.
        
        Returns:
            DataFrame with load pattern information
        """
        try:
            ret = self.model.LoadPatterns.GetNameList()
            
            if ret[0] == 0:
                logger.warning("No load patterns found")
                return pd.DataFrame(columns=['Name', 'Type', 'SelfWeightMult'])
            
            pattern_names = ret[1]
            data = []
            
            for name in pattern_names:
                info = self.model.LoadPatterns.GetLoadType(name)
                sw_mult = self.model.LoadPatterns.GetSelfWTMultiplier(name)
                
                data.append({
                    'Name': name,
                    'Type': info[0],
                    'SelfWeightMult': sw_mult[0]
                })
            
            df = pd.DataFrame(data)
            logger.debug(f"Retrieved {len(df)} load patterns")
            return df
            
        except Exception as e:
            raise LoadError(f"Failed to get load patterns: {str(e)}")
    
    # ==================== POINT LOADS ====================
    
    def add_point_load(
        self,
        point_name: str,
        load_pattern: str,
        force_x: float = 0.0,
        force_y: float = 0.0,
        force_z: float = 0.0,
        moment_x: float = 0.0,
        moment_y: float = 0.0,
        moment_z: float = 0.0,
        replace: bool = True
    ) -> None:
        """
        Apply force/moment load to a point.
        
        Args:
            point_name: Name of point
            load_pattern: Load pattern name
            force_x, force_y, force_z: Force components
            moment_x, moment_y, moment_z: Moment components
            replace: If True, replaces existing loads. If False, adds to existing.
        """
        try:
            ret = self.model.PointObj.SetLoadForce(
                point_name,
                load_pattern,
                [force_x, force_y, force_z, moment_x, moment_y, moment_z],
                replace
            )
            
            if ret == 0:
                logger.info(f"Applied point load to {point_name} in pattern {load_pattern}")
            else:
                raise LoadError(f"Failed to apply point load to {point_name}")
                
        except Exception as e:
            raise LoadError(f"Error applying point load: {str(e)}")
    
    # ==================== FRAME LOADS ====================
    
    def add_frame_distributed_load(
        self,
        frame_name: str,
        load_pattern: str,
        load_type: int,
        direction: int,
        distance1: float,
        distance2: float,
        value1: float,
        value2: float,
        coord_system: str = "Global",
        relative_distance: bool = True,
        replace: bool = True
    ) -> None:
        """
        Apply distributed load to a frame element.
        
        Args:
            frame_name: Name of frame
            load_pattern: Load pattern name
            load_type: 1=Force, 2=Moment
            direction: Load direction (1-6 for forces/moments in local axes, 
                      7-12 for global, 13-15 for projected)
            distance1: Start distance along frame
            distance2: End distance along frame
            value1: Load value at start
            value2: Load value at end
            coord_system: Coordinate system ("Global" or "Local")
            relative_distance: If True, distances are relative (0-1)
            replace: If True, replaces existing loads
        """
        try:
            ret = self.model.FrameObj.SetLoadDistributed(
                frame_name,
                load_pattern,
                load_type,
                direction,
                distance1,
                distance2,
                value1,
                value2,
                coord_system,
                relative_distance,
                replace
            )
            
            if ret == 0:
                logger.info(
                    f"Applied distributed load to frame {frame_name}: "
                    f"{value1} to {value2} in pattern {load_pattern}"
                )
            else:
                raise LoadError(f"Failed to apply distributed load to {frame_name}")
                
        except Exception as e:
            raise LoadError(f"Error applying frame distributed load: {str(e)}")
    
    def add_frame_point_load(
        self,
        frame_name: str,
        load_pattern: str,
        load_type: int,
        direction: int,
        distance: float,
        value: float,
        coord_system: str = "Global",
        relative_distance: bool = True,
        replace: bool = True
    ) -> None:
        """
        Apply point load to a frame element.
        
        Args:
            frame_name: Name of frame
            load_pattern: Load pattern name
            load_type: 1=Force, 2=Moment
            direction: Load direction
            distance: Distance along frame
            value: Load value
            coord_system: Coordinate system
            relative_distance: If True, distance is relative (0-1)
            replace: If True, replaces existing loads
        """
        try:
            ret = self.model.FrameObj.SetLoadPoint(
                frame_name,
                load_pattern,
                load_type,
                direction,
                distance,
                value,
                coord_system,
                relative_distance,
                replace
            )
            
            if ret == 0:
                logger.info(
                    f"Applied point load to frame {frame_name}: "
                    f"{value} at {distance} in pattern {load_pattern}"
                )
            else:
                raise LoadError(f"Failed to apply point load to {frame_name}")
                
        except Exception as e:
            raise LoadError(f"Error applying frame point load: {str(e)}")
    
    # ==================== AREA LOADS ====================
    
    def add_area_uniform_load(
        self,
        area_name: str,
        load_pattern: str,
        value: float,
        direction: int = 6,  # 6 = Gravity (local -3)
        replace: bool = True
    ) -> None:
        """
        Apply uniform load to an area element.
        
        Args:
            area_name: Name of area
            load_pattern: Load pattern name
            value: Load value (force per unit area)
            direction: Load direction (6 = Gravity)
            replace: If True, replaces existing loads
        """
        try:
            ret = self.model.AreaObj.SetLoadUniform(
                area_name,
                load_pattern,
                value,
                direction,
                replace
            )
            
            if ret == 0:
                logger.info(
                    f"Applied uniform load to area {area_name}: "
                    f"{value} in pattern {load_pattern}"
                )
            else:
                raise LoadError(f"Failed to apply uniform load to {area_name}")
                
        except Exception as e:
            raise LoadError(f"Error applying area uniform load: {str(e)}")
    
    # ==================== LOAD COMBINATIONS ====================
    
    def add_load_combination(
        self,
        name: str,
        combo_type: int = 0
    ) -> None:
        """
        Add a load combination.
        
        Args:
            name: Combination name
            combo_type: Type (0=Linear Add, 1=Envelope, 2=Absolute Add, etc.)
        """
        try:
            ret = self.model.RespCombo.Add(name, combo_type)
            if ret == 0:
                logger.info(f"Added load combination: {name} (type={combo_type})")
            else:
                raise LoadError(f"Failed to add load combination {name}")
                
        except Exception as e:
            raise LoadError(f"Error adding load combination: {str(e)}")
    
    def set_combination_case(
        self,
        combo_name: str,
        case_name: str,
        scale_factor: float
    ) -> None:
        """
        Add a load case to a combination with scale factor.
        
        Args:
            combo_name: Name of combination
            case_name: Name of load case/pattern to add
            scale_factor: Multiplier for the case
        """
        try:
            # Get existing cases in combination
            ret = self.model.RespCombo.GetCaseList(combo_name)
            
            # Add new case
            case_type = 0  # LoadCase
            ret2 = self.model.RespCombo.SetCaseList(
                combo_name,
                case_type,
                case_name,
                scale_factor
            )
            
            if ret2 == 0:
                logger.info(
                    f"Added {case_name} to combo {combo_name} "
                    f"with factor {scale_factor}"
                )
            else:
                raise LoadError(f"Failed to add case to combination")
                
        except Exception as e:
            raise LoadError(f"Error setting combination case: {str(e)}")