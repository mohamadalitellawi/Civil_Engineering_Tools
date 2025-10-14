"""
ETABS results extraction module.

Handles extraction and processing of analysis results.
"""

from typing import Optional, List, Tuple
from loguru import logger
import pandas as pd
import numpy as np

from ..core.exceptions import ResultsError


class ETABSResults:
    """
    Handler for ETABS analysis results.
    
    This class provides methods to extract and process analysis results.
    """
    
    def __init__(self, model):
        """
        Initialize results handler.
        
        Args:
            model: ETABS SapModel object
        """
        self.model = model
        logger.info("ETABS Results handler initialized")
    
    def _check_analysis_results(self) -> bool:
        """Check if analysis results are available."""
        try:
            ret = self.model.Results.Setup.DeselectAllCasesAndCombosForOutput()
            # If we can access results, they exist
            return True
        except:
            return False
    
    # ==================== JOINT/POINT RESULTS ====================
    
    def get_joint_reactions(
        self,
        load_case: Optional[str] = None
    ) -> pd.DataFrame:
        """
        Get joint reactions.
        
        Args:
            load_case: Specific load case/combo name. If None, gets all.
        
        Returns:
            DataFrame with joint reactions
        """
        try:
            if not self._check_analysis_results():
                raise ResultsError("No analysis results available. Run analysis first.")
            
            # Select output for specific case if provided
            if load_case:
                self.model.Results.Setup.DeselectAllCasesAndCombosForOutput()
                self.model.Results.Setup.SetCaseSelectedForOutput(load_case)
            
            # Get reactions
            ret = self.model.Results.JointReact()
            
            if ret[0] == 0:
                logger.warning("No joint reactions found")
                return pd.DataFrame()
            
            # Parse results
            num_results = ret[0]
            data = []
            
            for i in range(num_results):
                data.append({
                    'Joint': ret[1][i],
                    'LoadCase': ret[2][i],
                    'StepType': ret[3][i],
                    'StepNum': ret[4][i],
                    'F1': ret[5][i],
                    'F2': ret[6][i],
                    'F3': ret[7][i],
                    'M1': ret[8][i],
                    'M2': ret[9][i],
                    'M3': ret[10][i]
                })
            
            df = pd.DataFrame(data)
            logger.info(f"Retrieved {len(df)} joint reaction results")
            return df
            
        except Exception as e:
            raise ResultsError(f"Failed to get joint reactions: {str(e)}")
    
    def get_joint_displacements(
        self,
        load_case: Optional[str] = None
    ) -> pd.DataFrame:
        """
        Get joint displacements.
        
        Args:
            load_case: Specific load case/combo name. If None, gets all.
        
        Returns:
            DataFrame with joint displacements
        """
        try:
            if not self._check_analysis_results():
                raise ResultsError("No analysis results available. Run analysis first.")
            
            if load_case:
                self.model.Results.Setup.DeselectAllCasesAndCombosForOutput()
                self.model.Results.Setup.SetCaseSelectedForOutput(load_case)
            
            ret = self.model.Results.JointDispl()
            
            if ret[0] == 0:
                logger.warning("No joint displacements found")
                return pd.DataFrame()
            
            num_results = ret[0]
            data = []
            
            for i in range(num_results):
                data.append({
                    'Joint': ret[1][i],
                    'LoadCase': ret[2][i],
                    'StepType': ret[3][i],
                    'StepNum': ret[4][i],
                    'U1': ret[5][i],
                    'U2': ret[6][i],
                    'U3': ret[7][i],
                    'R1': ret[8][i],
                    'R2': ret[9][i],
                    'R3': ret[10][i]
                })
            
            df = pd.DataFrame(data)
            logger.info(f"Retrieved {len(df)} joint displacement results")
            return df
            
        except Exception as e:
            raise ResultsError(f"Failed to get joint displacements: {str(e)}")
    
    # ==================== FRAME RESULTS ====================
    
    def get_frame_forces(
        self,
        load_case: Optional[str] = None,
        frame_name: Optional[str] = None
    ) -> pd.DataFrame:
        """
        Get frame element forces.
        
        Args:
            load_case: Specific load case/combo name
            frame_name: Specific frame name. If None, gets all frames.
        
        Returns:
            DataFrame with frame forces
        """
        try:
            if not self._check_analysis_results():
                raise ResultsError("No analysis results available. Run analysis first.")
            
            if load_case:
                self.model.Results.Setup.DeselectAllCasesAndCombosForOutput()
                self.model.Results.Setup.SetCaseSelectedForOutput(load_case)
            
            if frame_name:
                ret = self.model.Results.FrameForce(frame_name, 0)  # 0 = Object element
            else:
                ret = self.model.Results.FrameForce("", 0)  # All frames
            
            if ret[0] == 0:
                logger.warning("No frame forces found")
                return pd.DataFrame()
            
            num_results = ret[0]
            data = []
            
            for i in range(num_results):
                data.append({
                    'Frame': ret[1][i],
                    'LoadCase': ret[2][i],
                    'StepType': ret[3][i],
                    'StepNum': ret[4][i],
                    'ObjectType': ret[5][i],
                    'Distance': ret[6][i],
                    'P': ret[7][i],      # Axial force
                    'V2': ret[8][i],     # Shear force
                    'V3': ret[9][i],     # Shear force
                    'T': ret[10][i],     # Torsion
                    'M2': ret[11][i],    # Moment
                    'M3': ret[12][i]     # Moment
                })
            
            df = pd.DataFrame(data)
            logger.info(f"Retrieved {len(df)} frame force results")
            return df
            
        except Exception as e:
            raise ResultsError(f"Failed to get frame forces: {str(e)}")
    
    def get_frame_design_results(
        self,
        frame_name: Optional[str] = None
    ) -> pd.DataFrame:
        """
        Get frame design results (steel or concrete).
        
        Args:
            frame_name: Specific frame name. If None, gets all frames.
        
        Returns:
            DataFrame with design results
        """
        try:
            if not self._check_analysis_results():
                raise ResultsError("No analysis results available. Run analysis first.")
            
            # Try to get concrete design results first
            try:
                if frame_name:
                    ret = self.model.DesignConcrete.GetSummaryResults(frame_name, 0)
                else:
                    # Get all frames
                    frames = self.model.FrameObj.GetNameList()
                    if frames[0] == 0:
                        return pd.DataFrame()
                    
                    all_data = []
                    for fname in frames[1]:
                        try:
                            ret = self.model.DesignConcrete.GetSummaryResults(fname, 0)
                            if ret[0] == 0:
                                all_data.append({
                                    'Frame': fname,
                                    'Status': 'Not Designed'
                                })
                            else:
                                all_data.append({
                                    'Frame': fname,
                                    'Option': ret[1],
                                    'Location': ret[2],
                                    'PMMCombo': ret[3],
                                    'PMMArea': ret[4],
                                    'PMMRatio': ret[5],
                                    'VMajorCombo': ret[6],
                                    'VmajorArea': ret[7]
                                })
                        except:
                            continue
                    
                    df = pd.DataFrame(all_data)
                    logger.info(f"Retrieved design results for {len(df)} frames")
                    return df
                    
            except Exception as e:
                logger.warning(f"Concrete design results not available: {str(e)}")
                return pd.DataFrame()
                
        except Exception as e:
            raise ResultsError(f"Failed to get frame design results: {str(e)}")
    
    # ==================== AREA/SHELL RESULTS ====================
    
    def get_area_forces(
        self,
        load_case: Optional[str] = None,
        area_name: Optional[str] = None
    ) -> pd.DataFrame:
        """
        Get area/shell element forces.
        
        Args:
            load_case: Specific load case/combo name
            area_name: Specific area name. If None, gets all areas.
        
        Returns:
            DataFrame with area forces
        """
        try:
            if not self._check_analysis_results():
                raise ResultsError("No analysis results available. Run analysis first.")
            
            if load_case:
                self.model.Results.Setup.DeselectAllCasesAndCombosForOutput()
                self.model.Results.Setup.SetCaseSelectedForOutput(load_case)
            
            if area_name:
                ret = self.model.Results.AreaForceShell(area_name, 0)
            else:
                ret = self.model.Results.AreaForceShell("", 0)  # All areas
            
            if ret[0] == 0:
                logger.warning("No area forces found")
                return pd.DataFrame()
            
            num_results = ret[0]
            data = []
            
            for i in range(num_results):
                data.append({
                    'Area': ret[1][i],
                    'LoadCase': ret[2][i],
                    'StepType': ret[3][i],
                    'StepNum': ret[4][i],
                    'ObjectType': ret[5][i],
                    'F11': ret[6][i],    # Membrane force
                    'F22': ret[7][i],    # Membrane force
                    'F12': ret[8][i],    # Membrane force
                    'M11': ret[9][i],    # Bending moment
                    'M22': ret[10][i],   # Bending moment
                    'M12': ret[11][i],   # Bending moment
                    'V13': ret[12][i],   # Shear force
                    'V23': ret[13][i]    # Shear force
                })
            
            df = pd.DataFrame(data)
            logger.info(f"Retrieved {len(df)} area force results")
            return df
            
        except Exception as e:
            raise ResultsError(f"Failed to get area forces: {str(e)}")
    
    def get_area_stresses(
        self,
        load_case: Optional[str] = None,
        area_name: Optional[str] = None
    ) -> pd.DataFrame:
        """
        Get area/shell element stresses.
        
        Args:
            load_case: Specific load case/combo name
            area_name: Specific area name. If None, gets all areas.
        
        Returns:
            DataFrame with area stresses
        """
        try:
            if not self._check_analysis_results():
                raise ResultsError("No analysis results available. Run analysis first.")
            
            if load_case:
                self.model.Results.Setup.DeselectAllCasesAndCombosForOutput()
                self.model.Results.Setup.SetCaseSelectedForOutput(load_case)
            
            if area_name:
                ret = self.model.Results.AreaStressShell(area_name, 0)
            else:
                ret = self.model.Results.AreaStressShell("", 0)
            
            if ret[0] == 0:
                logger.warning("No area stresses found")
                return pd.DataFrame()
            
            num_results = ret[0]
            data = []
            
            for i in range(num_results):
                data.append({
                    'Area': ret[1][i],
                    'LoadCase': ret[2][i],
                    'StepType': ret[3][i],
                    'StepNum': ret[4][i],
                    'ObjectType': ret[5][i],
                    'Location': ret[6][i],  # Top/Bottom
                    'S11': ret[7][i],
                    'S22': ret[8][i],
                    'S12': ret[9][i],
                    'SMax': ret[10][i],
                    'SMin': ret[11][i],
                    'Angle': ret[12][i],
                    'SVM': ret[13][i]  # Von Mises stress
                })
            
            df = pd.DataFrame(data)
            logger.info(f"Retrieved {len(df)} area stress results")
            return df
            
        except Exception as e:
            raise ResultsError(f"Failed to get area stresses: {str(e)}")
    
    # ==================== STORY RESULTS ====================
    
    def get_story_forces(
        self,
        load_case: Optional[str] = None,
        story: Optional[str] = None
    ) -> pd.DataFrame:
        """
        Get story forces (for lateral analysis).
        
        Args:
            load_case: Specific load case/combo name
            story: Specific story name. If None, gets all stories.
        
        Returns:
            DataFrame with story forces
        """
        try:
            if not self._check_analysis_results():
                raise ResultsError("No analysis results available. Run analysis first.")
            
            if load_case:
                self.model.Results.Setup.DeselectAllCasesAndCombosForOutput()
                self.model.Results.Setup.SetCaseSelectedForOutput(load_case)
            
            if story:
                ret = self.model.Results.StoryForce(story)
            else:
                ret = self.model.Results.StoryForce("")  # All stories
            
            if ret[0] == 0:
                logger.warning("No story forces found")
                return pd.DataFrame()
            
            num_results = ret[0]
            data = []
            
            for i in range(num_results):
                data.append({
                    'Story': ret[1][i],
                    'LoadCase': ret[2][i],
                    'Location': ret[3][i],
                    'VX': ret[4][i],     # Shear X
                    'VY': ret[5][i],     # Shear Y
                    'T': ret[6][i],      # Torsion
                    'MX': ret[7][i],     # Moment X
                    'MY': ret[8][i]      # Moment Y
                })
            
            df = pd.DataFrame(data)
            logger.info(f"Retrieved {len(df)} story force results")
            return df
            
        except Exception as e:
            raise ResultsError(f"Failed to get story forces: {str(e)}")
    
    # ==================== MODAL RESULTS ====================
    
    def get_modal_periods(self) -> pd.DataFrame:
        """
        Get modal analysis periods and frequencies.
        
        Returns:
            DataFrame with modal periods
        """
        try:
            if not self._check_analysis_results():
                raise ResultsError("No analysis results available. Run analysis first.")
            
            ret = self.model.Results.ModalPeriod()
            
            if ret[0] == 0:
                logger.warning("No modal results found")
                return pd.DataFrame()
            
            num_modes = ret[0]
            data = []
            
            for i in range(num_modes):
                data.append({
                    'LoadCase': ret[1][i],
                    'StepType': ret[2][i],
                    'StepNum': ret[3][i],
                    'Period': ret[4][i],
                    'Frequency': ret[5][i],
                    'CircFreq': ret[6][i],
                    'EigenValue': ret[7][i]
                })
            
            df = pd.DataFrame(data)
            logger.info(f"Retrieved {len(df)} modal periods")
            return df
            
        except Exception as e:
            raise ResultsError(f"Failed to get modal periods: {str(e)}")
    
    def get_modal_participation_factors(self) -> pd.DataFrame:
        """
        Get modal participation factors and mass ratios.
        
        Returns:
            DataFrame with participation factors
        """
        try:
            if not self._check_analysis_results():
                raise ResultsError("No analysis results available. Run analysis first.")
            
            ret = self.model.Results.ModalParticipationFactors()
            
            if ret[0] == 0:
                logger.warning("No modal participation factors found")
                return pd.DataFrame()
            
            num_modes = ret[0]
            data = []
            
            for i in range(num_modes):
                data.append({
                    'LoadCase': ret[1][i],
                    'StepType': ret[2][i],
                    'StepNum': ret[3][i],
                    'Period': ret[4][i],
                    'UX': ret[5][i],
                    'UY': ret[6][i],
                    'UZ': ret[7][i],
                    'RX': ret[8][i],
                    'RY': ret[9][i],
                    'RZ': ret[10][i],
                    'ModalMass': ret[11][i],
                    'ModalStiff': ret[12][i]
                })
            
            df = pd.DataFrame(data)
            
            # Calculate cumulative mass participation
            df['CumUX'] = df['UX'].cumsum()
            df['CumUY'] = df['UY'].cumsum()
            df['CumUZ'] = df['UZ'].cumsum()
            
            logger.info(f"Retrieved {len(df)} modal participation factors")
            return df
            
        except Exception as e:
            raise ResultsError(f"Failed to get modal participation factors: {str(e)}")
    
    # ==================== UTILITY METHODS ====================
    
    def export_results_to_excel(
        self,
        file_path: str,
        load_case: Optional[str] = None
    ) -> None:
        """
        Export all results to an Excel file with multiple sheets.
        
        Args:
            file_path: Path to save Excel file
            load_case: Specific load case to export. If None, exports all.
        """
        try:
            logger.info(f"Exporting results to {file_path}...")
            
            with pd.ExcelWriter(file_path, engine='openpyxl') as writer:
                # Joint results
                try:
                    df_reactions = self.get_joint_reactions(load_case)
                    if not df_reactions.empty:
                        df_reactions.to_excel(writer, sheet_name='Joint_Reactions', index=False)
                except Exception as e:
                    logger.warning(f"Could not export joint reactions: {str(e)}")
                
                try:
                    df_displ = self.get_joint_displacements(load_case)
                    if not df_displ.empty:
                        df_displ.to_excel(writer, sheet_name='Joint_Displacements', index=False)
                except Exception as e:
                    logger.warning(f"Could not export joint displacements: {str(e)}")
                
                # Frame results
                try:
                    df_forces = self.get_frame_forces(load_case)
                    if not df_forces.empty:
                        df_forces.to_excel(writer, sheet_name='Frame_Forces', index=False)
                except Exception as e:
                    logger.warning(f"Could not export frame forces: {str(e)}")
                
                # Area results
                try:
                    df_area_forces = self.get_area_forces(load_case)
                    if not df_area_forces.empty:
                        df_area_forces.to_excel(writer, sheet_name='Area_Forces', index=False)
                except Exception as e:
                    logger.warning(f"Could not export area forces: {str(e)}")
                
                # Modal results (if available)
                try:
                    df_periods = self.get_modal_periods()
                    if not df_periods.empty:
                        df_periods.to_excel(writer, sheet_name='Modal_Periods', index=False)
                except Exception as e:
                    logger.warning(f"Could not export modal periods: {str(e)}")
            
            logger.info(f"Results exported successfully to {file_path}")
            
        except Exception as e:
            raise ResultsError(f"Failed to export results: {str(e)}")