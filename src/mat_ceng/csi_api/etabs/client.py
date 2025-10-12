# src/csi_api/etabs/client.py

import os
from ..core.connection import connect_to_csi_api
from ..exceptions import ConnectionError, ModelError
from ..config import load_config
from ..core.utils import setup_logger
from ..core.units import detect_units_from_etabs

class ETABSClient:
    def __init__(self, config_path=None):
        self.config = load_config(config_path)
        self.logger = setup_logger(self.config)

        conn_config = self.config.get("connection", {})
        self.attach_to_existing = conn_config.get("attach_to_existing", True)
        self.timeout = conn_config.get("launch_timeout_sec", 10)

        paths = self.config.get("software_paths", {})
        self.exe_path = paths.get("etabs")
        self.dll_path = paths.get("etabs_dll")

        self._etabs_object = None
        self._sap_model = None
        self._etabs_dll_lib = None
        self._is_connected = False

    def connect(self):
        try:
            self._etabs_object, self._sap_model, self._etabs_dll_lib = connect_to_csi_api(
                prog_id="CSI.ETABS.API.ETABSObject",
                dll_path=self.dll_path,
                exe_path=self.exe_path,
                attach_to_existing=self.attach_to_existing,
                timeout=self.timeout
            )
            
            self._is_connected = True

            self._units = detect_units_from_etabs(self._sap_model, self._etabs_object, self._etabs_dll_lib)

            self.logger.info("ETABS connection established.")
            self.logger.info(f"Model units detected: force={self._units['force']}, length={self._units['length']}, moment={self._units['moment']}")
            
        except Exception as e:
            raise ConnectionError(f"ETABS connection failed: {e}") from e

    def __enter__(self):
        if not self._is_connected:
            self.connect()
        return self

    def __exit__(self, exc_type, exc_val, exc_tb):
        self.close()

    def close(self):
        if self._etabs_object:
            if not self.attach_to_existing:
                self._etabs_object.ApplicationExit(False)
            self._etabs_object = None
            self._sap_model = None
            self._etabs_dll_lib = None
            self._is_connected = False
            self.logger.info("ETABS connection closed.")

    def get_story_names(self):
        if not self._is_connected:
            raise ModelError("Not connected to ETABS")
        try:
            stories_count = 0
            stories_names = []
            ret = self._sap_model.Story.GetNameList(stories_count, stories_names)
            return list(ret[2])
        except Exception as e:
            raise ModelError(f"Failed to get story names: {e}") from e

    def add_load_pattern(self, name, load_type=1):
        try:
            ret = self._sap_model.LoadPatterns.Add(name, load_type)
            if ret != 0:
                raise ModelError(f"Failed to add load pattern '{name}'")
            self.logger.info(f"Added load pattern: {name}")
        except Exception as e:
            raise ModelError(f"Error adding load pattern: {e}") from e

    def run_analysis(self):
        ret = self._sap_model.Analyze.RunAnalysis()
        if ret != 0:
            raise ModelError("Analysis failed")
        self.logger.info("Analysis completed successfully.")

    # Add these methods inside ETABSClient class in etabs/client.py

    def export_joint_reactions(self, load_case, filepath):
        """
        Export joint reactions for a given load case to CSV.
        
        Args:
            load_case: name of load case (e.g., "DEAD")
            filepath: output CSV path
        """
        if not self._is_connected:
            raise ModelError("Not connected to ETABS")

        try:
            # Get all point objects
            points = self._sap_model.PointObj.GetNameList()
            num_points = points[0]
            point_names = points[1]

            reactions = []
            for name in point_names:
                # Get reaction (Fx, Fy, Fz, Mx, My, Mz)
                ret = self._sap_model.PointElm.GetJointReaction(name, load_case, 0)
                if ret[0] == 0:  # Success
                    fx, fy, fz, mx, my, mz = ret[2:8]
                    reactions.append({
                        "Point": name,
                        "LoadCase": load_case,
                        "Fx_kN": fx,
                        "Fy_kN": fy,
                        "Fz_kN": fz,
                        "Mx_kNm": mx,
                        "My_kNm": my,
                        "Mz_kNm": mz
                    })

            from ..core.exporter import export_to_csv
            output_path = export_to_csv(reactions, filepath)
            self.logger.info(f"Joint reactions exported to: {output_path}")
            return output_path

        except Exception as e:
            raise ModelError(f"Failed to export joint reactions: {e}") from e

    def export_story_shears(self, load_case, filepath):
        """Export story shears to CSV."""
        if not self._is_connected:
            raise ModelError("Not connected to ETABS")

        try:
            stories = self._sap_model.Story.GetStories()
            story_names = list(stories[1])
            shears = []
            for story in story_names:
                ret = self._sap_model.Story.GetDiaphragmCenterOfMass(story)
                if ret[0] == 0:
                    vx, vy = self._sap_model.Story.GetStoryShear(story, load_case)[:2]
                    shears.append({
                        "Story": story,
                        "LoadCase": load_case,
                        "Vx_kN": vx,
                        "Vy_kN": vy
                    })

            from ..core.exporter import export_to_csv
            output_path = export_to_csv(shears, filepath)
            self.logger.info(f"Story shears exported to: {output_path}")
            return output_path

        except Exception as e:
            raise ModelError(f"Failed to export story shears: {e}") from e

    def export_frame_forces(self, load_case, filepath):
        """Export frame end forces to CSV."""
        if not self._is_connected:
            raise ModelError("Not connected to ETABS")

        try:
            frames = self._sap_model.FrameObj.GetNameList()
            frame_names = frames[1]
            forces = []

            for name in frame_names:
                ret = self._sap_model.FrameObj.GetSection(name)
                if ret[0] != 0:
                    continue  # Skip if no section

                # Get forces at start (0) and end (1)
                for station in [0, 1]:
                    force = self._sap_model.FrameObj.GetFrameForce(name, load_case, station)
                    if force[0] == 0:
                        p, v2, v3, t, m2, m3 = force[2:8]
                        loc = "Start" if station == 0 else "End"
                        forces.append({
                            "Frame": name,
                            "Location": loc,
                            "LoadCase": load_case,
                            "P_kN": p,
                            "V2_kN": v2,
                            "V3_kN": v3,
                            "T_kNm": t,
                            "M2_kNm": m2,
                            "M3_kNm": m3
                        })

            from ..core.exporter import export_to_csv
            output_path = export_to_csv(forces, filepath)
            self.logger.info(f"Frame forces exported to: {output_path}")
            return output_path

        except Exception as e:
            raise ModelError(f"Failed to export frame forces: {e}") from e