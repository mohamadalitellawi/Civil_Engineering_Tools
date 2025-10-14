"""
Complete ETABS workflow example.

This example demonstrates:
1. Connecting to ETABS
2. Creating a simple building model
3. Defining materials and sections
4. Adding structural elements
5. Applying loads
6. Running analysis
7. Extracting results
8. Exporting to Excel
"""

from pathlib import Path
from mat_ceng.csi_toolkit.etabs import ETABSAPI
from mat_ceng.csi_toolkit.etabs.elements import ETABSElements
from mat_ceng.csi_toolkit.etabs.loads import ETABSLoads
from mat_ceng.csi_toolkit.etabs.results import ETABSResults
from mat_ceng.csi_toolkit.utils.logging_config import setup_logging
from mat_ceng.csi_toolkit.utils.helpers import get_unit_codes, get_load_type_code
from loguru import logger


def main():
    """Main execution function."""
    
    # Setup logging
    setup_logging(log_level="INFO", console_output=True)
    
    logger.info("="*60)
    logger.info("ETABS Complete Workflow Example")
    logger.info("="*60)
    
    # Initialize ETABS API (will use default installation path)
    # If ETABS is installed elsewhere, provide path:
    # etabs = ETABSAPI(installation_path=r"C:\Your\Custom\Path")
    etabs = ETABSAPI()
    
    try:
        # ===== STEP 1: CONNECT TO ETABS =====
        logger.info("\nStep 1: Connecting to ETABS...")
        etabs.connect(
            attach_to_existing=False,  # Create new instance
            visible=True,              # Show GUI
            model_path=None            # Create blank model
        )
        
        # ===== STEP 2: CREATE MODEL FROM TEMPLATE =====
        logger.info("\nStep 2: Creating model from template...")
        etabs.create_template_model(
            template_type="BeamSlab",
            num_stories=5,
            story_height=3.5,  # meters
            num_bays_x=3,
            bay_width_x=6.0,   # meters
            num_bays_y=3,
            bay_width_y=6.0    # meters
        )
        
        # Set units to kN-m
        force_code, length_code = get_unit_codes('kN', 'm')
        etabs.set_model_units(force_code, length_code)
        
        # Set project information
        etabs.set_project_info("Company Name", "My Engineering Firm")
        etabs.set_project_info("Engineer", "John Doe, P.E.")
        etabs.set_project_info("Project Name", "5-Story Office Building")
        
        # Unlock model for editing
        etabs.unlock_model()
        
        # ===== STEP 3: DEFINE MATERIALS AND SECTIONS =====
        logger.info("\nStep 3: Defining materials and sections...")
        elements = ETABSElements(etabs.model)
        
        # Add concrete material (C30/37)
        elements.add_material(
            name="C30",
            material_type=2,  # Concrete
            region="ACI 318-14"
        )
        
        # Add steel material (S355)
        elements.add_material(
            name="S355",
            material_type=1,  # Steel
            region="AISC 360-16"
        )
        
        # Define column section (400mm x 400mm)
        elements.add_frame_section_rectangular(
            name="COL400x400",
            material="C30",
            depth=0.4,
            width=0.4
        )
        
        # Define beam section (300mm x 600mm)
        elements.add_frame_section_rectangular(
            name="BEAM300x600",
            material="C30",
            depth=0.6,
            width=0.3
        )
        
        # Define slab section (200mm thick)
        elements.add_slab_section(
            name="SLAB200",
            slab_type=1,  # Shell-Thick
            material="C30",
            thickness=0.2
        )
        
        logger.info("Materials and sections defined successfully")
        
        # Get element counts
        counts = etabs.get_element_count()
        logger.info(f"Current model: {counts}")
        
        # ===== STEP 4: MODIFY FRAME SECTIONS =====
        logger.info("\nStep 4: Assigning frame sections...")
        
        # Get all frames
        frames_df = elements.get_all_frames()
        logger.info(f"Found {len(frames_df)} frame elements")
        
        # Assign sections based on frame type (simplified logic)
        # In a real project, you'd identify frames more carefully
        for idx, frame in frames_df.iterrows():
            frame_name = frame['Name']
            # Simplified: assume vertical frames are columns
            point1_coords = etabs.model.PointObj.GetCoordCartesian(frame['Point1'])
            point2_coords = etabs.model.PointObj.GetCoordCartesian(frame['Point2'])
            
            # Check if frame is vertical (Z coordinates differ significantly)
            if abs(point2_coords[2] - point1_coords[2]) > 1.0:
                elements.set_frame_section(frame_name, "COL400x400")
            else:
                elements.set_frame_section(frame_name, "BEAM300x600")
        
        logger.info("Frame sections assigned")
        
        # ===== STEP 5: DEFINE LOADS =====
        logger.info("\nStep 5: Defining loads...")
        loads = ETABSLoads(etabs.model)
        
        # Add load patterns
        loads.add_load_pattern(
            name="DEAD",
            load_type=get_load_type_code("DEAD"),
            self_weight_multiplier=1.0  # Include self-weight
        )
        
        loads.add_load_pattern(
            name="SDL",  # Superimposed Dead Load
            load_type=get_load_type_code("SUPERDEAD"),
            self_weight_multiplier=0.0
        )
        
        loads.add_load_pattern(
            name="LIVE",
            load_type=get_load_type_code("LIVE"),
            self_weight_multiplier=0.0
        )
        
        loads.add_load_pattern(
            name="WIND_X",
            load_type=get_load_type_code("WIND"),
            self_weight_multiplier=0.0
        )
        
        # Apply uniform loads to all slabs
        areas_df = elements.get_all_areas()
        logger.info(f"Found {len(areas_df)} area elements")
        
        for idx, area in areas_df.iterrows():
            area_name = area['Name']
            
            # SDL: 2 kN/m² (finishes, partitions, etc.)
            loads.add_area_uniform_load(
                area_name=area_name,
                load_pattern="SDL",
                value=2.0,  # kN/m²
                direction=6  # Gravity
            )
            
            # Live load: 3 kN/m² (office loading)
            loads.add_area_uniform_load(
                area_name=area_name,
                load_pattern="LIVE",
                value=3.0,  # kN/m²
                direction=6  # Gravity
            )
        
        logger.info("Area loads applied")
        
        # Apply distributed load to beams (partition wall load example)
        for idx, frame in frames_df.iterrows():
            frame_name = frame['Name']
            point1_coords = etabs.model.PointObj.GetCoordCartesian(frame['Point1'])
            point2_coords = etabs.model.PointObj.GetCoordCartesian(frame['Point2'])
            
            # Apply to horizontal beams only
            if abs(point2_coords[2] - point1_coords[2]) < 0.1:
                loads.add_frame_distributed_load(
                    frame_name=frame_name,
                    load_pattern="SDL",
                    load_type=1,  # Force
                    direction=6,  # Gravity
                    distance1=0.0,
                    distance2=1.0,
                    value1=-5.0,  # kN/m (wall load)
                    value2=-5.0,
                    relative_distance=True
                )
        
        logger.info("Frame loads applied")
        
        # ===== STEP 6: DEFINE LOAD COMBINATIONS =====
        logger.info("\nStep 6: Creating load combinations...")
        
        # Service load combination (for deflection checks)
        loads.add_load_combination(
            name="SERVICE",
            combo_type=0  # Linear Add
        )
        loads.set_combination_case("SERVICE", "DEAD", 1.0)
        loads.set_combination_case("SERVICE", "SDL", 1.0)
        loads.set_combination_case("SERVICE", "LIVE", 1.0)
        
        # Ultimate load combination (ACI 318)
        loads.add_load_combination(
            name="ULT_1.4D",
            combo_type=0
        )
        loads.set_combination_case("ULT_1.4D", "DEAD", 1.4)
        loads.set_combination_case("ULT_1.4D", "SDL", 1.4)
        
        loads.add_load_combination(
            name="ULT_1.2D+1.6L",
            combo_type=0
        )
        loads.set_combination_case("ULT_1.2D+1.6L", "DEAD", 1.2)
        loads.set_combination_case("ULT_1.2D+1.6L", "SDL", 1.2)
        loads.set_combination_case("ULT_1.2D+1.6L", "LIVE", 1.6)
        
        logger.info("Load combinations created")
        
        # ===== STEP 7: SAVE MODEL =====
        output_dir = Path("output")
        output_dir.mkdir(exist_ok=True)
        model_path = output_dir / "example_building.edb"
        
        logger.info(f"\nStep 7: Saving model to {model_path}...")
        etabs.save_model(str(model_path))
        
        # Refresh view
        etabs.refresh_view()
        
        # ===== STEP 8: RUN ANALYSIS =====
        logger.info("\nStep 8: Running analysis...")
        etabs.run_analysis()
        
        # ===== STEP 9: EXTRACT RESULTS =====
        logger.info("\nStep 9: Extracting results...")
        results = ETABSResults(etabs.model)
        
        # Get joint reactions
        logger.info("Extracting joint reactions...")
        reactions_df = results.get_joint_reactions(load_case="DEAD")
        logger.info(f"Extracted {len(reactions_df)} reaction results")
        
        if not reactions_df.empty:
            # Find maximum reactions
            max_fz = reactions_df.loc[reactions_df['F3'].abs().idxmax()]
            logger.info(f"Maximum vertical reaction: {max_fz['F3']:.2f} kN at joint {max_fz['Joint']}")
        
        # Get joint displacements
        logger.info("Extracting joint displacements...")
        displ_df = results.get_joint_displacements(load_case="SERVICE")
        logger.info(f"Extracted {len(displ_df)} displacement results")
        
        if not displ_df.empty:
            # Find maximum displacement
            max_uz = displ_df.loc[displ_df['U3'].abs().idxmax()]
            logger.info(f"Maximum vertical displacement: {max_uz['U3']*1000:.2f} mm at joint {max_uz['Joint']}")
        
        # Get frame forces
        logger.info("Extracting frame forces...")
        frame_forces_df = results.get_frame_forces(load_case="ULT_1.2D+1.6L")
        logger.info(f"Extracted {len(frame_forces_df)} frame force results")
        
        if not frame_forces_df.empty:
            # Find maximum moment
            max_moment = frame_forces_df.loc[frame_forces_df['M3'].abs().idxmax()]
            logger.info(f"Maximum moment: {max_moment['M3']:.2f} kN-m in frame {max_moment['Frame']}")
        
        # Get area forces
        logger.info("Extracting area forces...")
        area_forces_df = results.get_area_forces(load_case="ULT_1.2D+1.6L")
        logger.info(f"Extracted {len(area_forces_df)} area force results")
        
        # Get story forces (if any lateral loads exist)
        try:
            logger.info("Extracting story forces...")
            story_forces_df = results.get_story_forces()
            if not story_forces_df.empty:
                logger.info(f"Extracted {len(story_forces_df)} story force results")
        except Exception as e:
            logger.warning(f"Could not extract story forces: {str(e)}")
        
        # ===== STEP 10: EXPORT RESULTS TO EXCEL =====
        logger.info("\nStep 10: Exporting results to Excel...")
        excel_path = output_dir / "analysis_results.xlsx"
        results.export_results_to_excel(str(excel_path))
        logger.info(f"Results exported to {excel_path}")
        
        # ===== STEP 11: CREATE SUMMARY REPORT =====
        logger.info("\nStep 11: Creating summary report...")
        
        summary_path = output_dir / "summary_report.txt"
        with open(summary_path, 'w') as f:
            f.write("="*70 + "\n")
            f.write("ETABS ANALYSIS SUMMARY REPORT\n")
            f.write("="*70 + "\n\n")
            
            # Project info
            project_info = etabs.get_project_info()
            f.write("PROJECT INFORMATION:\n")
            f.write("-"*70 + "\n")
            for key, value in project_info.items():
                f.write(f"{key}: {value}\n")
            f.write("\n")
            
            # Model statistics
            f.write("MODEL STATISTICS:\n")
            f.write("-"*70 + "\n")
            f.write(f"Number of Stories: {counts['stories']}\n")
            f.write(f"Number of Points: {counts['points']}\n")
            f.write(f"Number of Frames: {counts['frames']}\n")
            f.write(f"Number of Areas: {counts['areas']}\n")
            f.write("\n")
            
            # Load patterns
            load_patterns = loads.get_all_load_patterns()
            f.write("LOAD PATTERNS:\n")
            f.write("-"*70 + "\n")
            for idx, lp in load_patterns.iterrows():
                f.write(f"{lp['Name']}: Type {lp['Type']}, SW Mult = {lp['SelfWeightMult']}\n")
            f.write("\n")
            
            # Key results
            f.write("KEY RESULTS:\n")
            f.write("-"*70 + "\n")
            
            if not reactions_df.empty:
                total_dead_load = reactions_df[reactions_df['LoadCase'] == 'DEAD']['F3'].sum()
                f.write(f"Total Dead Load Reactions: {total_dead_load:.2f} kN\n")
            
            if not displ_df.empty:
                max_displ = displ_df['U3'].abs().max()
                f.write(f"Maximum Vertical Displacement: {max_displ*1000:.2f} mm\n")
            
            if not frame_forces_df.empty:
                max_axial = frame_forces_df['P'].abs().max()
                max_shear = frame_forces_df[['V2', 'V3']].abs().max().max()
                max_moment_val = frame_forces_df[['M2', 'M3']].abs().max().max()
                f.write(f"Maximum Axial Force: {max_axial:.2f} kN\n")
                f.write(f"Maximum Shear Force: {max_shear:.2f} kN\n")
                f.write(f"Maximum Bending Moment: {max_moment_val:.2f} kN-m\n")
            
            f.write("\n")
            f.write("="*70 + "\n")
            f.write("End of Report\n")
        
        logger.info(f"Summary report saved to {summary_path}")
        
        # ===== FINAL MESSAGES =====
        logger.info("\n" + "="*60)
        logger.info("WORKFLOW COMPLETED SUCCESSFULLY!")
        logger.info("="*60)
        logger.info(f"\nOutputs saved in: {output_dir.absolute()}")
        logger.info(f"  - Model file: {model_path.name}")
        logger.info(f"  - Results Excel: {excel_path.name}")
        logger.info(f"  - Summary report: {summary_path.name}")
        logger.info("\nThe ETABS model is still open. Close it manually when done.")
        
    except Exception as e:
        logger.error(f"Error in workflow: {str(e)}", exc_info=True)
        raise
    
    finally:
        # Note: We're not disconnecting here so user can review the model
        # If you want automatic cleanup, uncomment the next line:
        # etabs.disconnect()
        logger.info("\nScript execution finished.")


if __name__ == "__main__":
    main()