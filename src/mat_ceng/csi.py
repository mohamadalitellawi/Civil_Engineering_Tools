# -*- coding: utf-8 -*-
"""
Module for interacting with Computers and Structures, Inc. (CSI) applications
like ETABS and SAP2000 using their OAPI via pythonnet.

Provides a CsiHelper class using class methods to manage a shared connection state.
"""

import clr
import logging
import sys
from typing import Optional, Dict, Any, List, Tuple, Union # Added Union

# Configure basic logging - Users can reconfigure this in their main script if needed
# Example: logging.basicConfig(level=logging.DEBUG, ...)
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    datefmt='%Y-%m-%d %H:%M:%S'
)
logger = logging.getLogger(__name__) # Use a module-specific logger

# --- Constants ---
DEFAULT_SAP_DLL = R'C:\Program Files\Computers and Structures\SAP2000 26\SAP2000v1.dll'
DEFAULT_ETABS_DLL = R'C:\Program Files\Computers and Structures\ETABS 22\ETABSv1.dll'
PROGID_ETABS = "CSI.ETABS.API.ETABSObject"
PROGID_SAP = "CSI.SAP2000.API.SapObject"

# --- CLR Setup ---
try:
    clr.AddReference("System.Runtime.InteropServices")
    from System.Runtime.InteropServices import Marshal
except ImportError as e:
    logger.critical(f"Failed to import System.Runtime.InteropServices: {e}. "
                    "Ensure pythonnet is installed and the .NET runtime is accessible.")
    Marshal = None # Flag that essential import failed
except Exception as e:
    logger.warning(f"Failed to add initial CLR reference 'System.Runtime.InteropServices': {e}")
    # Attempt to import Marshal anyway, might work if reference was added previously
    try:
        from System.Runtime.InteropServices import Marshal
    except ImportError:
        logger.critical("Failed to import System.Runtime.InteropServices after reference warning.")
        Marshal = None


class CsiHelper:
    """
    Manages a shared connection state to CSI applications (ETABS/SAP2000)
    using class methods.

    Provides methods to initialize the connection, connect to specific
    applications, manage units, and release the connection. Helper functions
    in this module utilize this class.

    Usage:
        1. (Optional but recommended) CsiHelper.initialize(etabs_dll=..., sap_dll=...)
        2. CsiHelper.connect_to_etabs() or CsiHelper.connect_to_sap()
        3. Use the returned SapModel object or helper functions (e.g., add_area).
        4. CsiHelper.release_connection() when done.
    """
    # --- Class Variables for State ---
    _sap_module: Optional[Any] = None
    _etabs_module: Optional[Any] = None
    _SapModel: Optional[Any] = None
    _mySapObject: Optional[Any] = None # Underlying COM object for SAP
    _myETABSObject: Optional[Any] = None # Underlying COM object for ETABS
    _etabs_units: Dict[str, Any] = {}
    _sap_units: Dict[str, Any] = {}
    _connected_to: Optional[str] = None # 'etabs' or 'sap'
    _initialized: bool = False
    _sap_dll_path: Optional[str] = None
    _etabs_dll_path: Optional[str] = None

    # --- Initialization ---
    @classmethod
    def initialize(cls,
                   sap_dll: Optional[str] = DEFAULT_SAP_DLL,
                   etabs_dll: Optional[str] = DEFAULT_ETABS_DLL) -> bool:
        """
        Initializes the CsiHelper class state (only runs once).
        Loads necessary CSI OAPI libraries and sets up unit dictionaries.

        This should ideally be called once at the start of your application.
        If not called explicitly, connection methods will attempt lazy
        initialization with default paths.

        Args:
            sap_dll (Optional[str]): Path to the SAP2000v1.dll. Defaults to a standard location.
                                     Set to None to skip loading SAP2000.
            etabs_dll (Optional[str]): Path to the ETABSv1.dll. Defaults to a standard location.
                                       Set to None to skip loading ETABS.

        Returns:
            bool: True if initialization was successful or already done, False otherwise.
        """
        if cls._initialized:
            logger.debug("CsiHelper already initialized.")
            return True
        if not Marshal: # Check if essential import failed
             logger.critical("Cannot initialize CsiHelper: System.Runtime.InteropServices not loaded.")
             return False

        logger.info("Initializing CsiHelper...")
        cls._sap_dll_path = sap_dll
        cls._etabs_dll_path = etabs_dll
        success_sap = False
        success_etabs = False

        # Load SAP2000 if path provided
        if sap_dll:
            try:
                logger.debug(f"Attempting to add reference: {sap_dll}")
                clr.AddReference(sap_dll)
                # Import dynamically to avoid import errors if DLL doesn't exist
                sap = __import__("SAP2000v1")
                cls._sap_module = sap
                # Populate units only if module loaded successfully
                cls._sap_units = {
                    'N_mm_C': cls._sap_module.eUnits.N_mm_C,
                    'kN_m_C': cls._sap_module.eUnits.kN_m_C,
                    # Add other common units as needed
                }
                logger.info(f"SAP2000 library loaded successfully from: {sap_dll}")
                success_sap = True
            except ImportError as e:
                 logger.error(f"Failed to import SAP2000v1 module after adding reference {sap_dll}: {e}. "
                              "Ensure the DLL exists and is compatible.")
            except Exception as e:
                logger.error(f"Failed to load SAP2000 library from {sap_dll}: {e}")
        else:
            logger.info("SAP2000 DLL path not provided, skipping SAP initialization.")

        # Load ETABS if path provided
        if etabs_dll:
            try:
                logger.debug(f"Attempting to add reference: {etabs_dll}")
                clr.AddReference(etabs_dll)
                etabs = __import__("ETABSv1")
                cls._etabs_module = etabs
                cls._etabs_units = {
                    'N_mm_C' : cls._etabs_module.eUnits.N_mm_C,
                    'kN_m_C' : cls._etabs_module.eUnits.kN_m_C,
                    # Add other common units as needed
                }
                logger.info(f"ETABS library loaded successfully from: {etabs_dll}")
                success_etabs = True
            except ImportError as e:
                 logger.error(f"Failed to import ETABSv1 module after adding reference {etabs_dll}: {e}. "
                              "Ensure the DLL exists and is compatible.")
            except Exception as e:
                logger.error(f"Failed to load ETABS library from {etabs_dll}: {e}")
        else:
             logger.info("ETABS DLL path not provided, skipping ETABS initialization.")

        # Mark as initialized if at least one library loaded
        if success_sap or success_etabs:
            cls._initialized = True
            logger.info("CsiHelper initialization complete.")
            return True
        else:
            logger.error("Initialization failed: Neither SAP2000 nor ETABS libraries could be loaded.")
            cls._initialized = False # Explicitly set to False
            return False

    @classmethod
    def _ensure_initialized(cls, required_app: Optional[str] = None) -> None:
        """
        Checks if initialized, attempts lazy init if not.
        Raises RuntimeError if initialization fails or required app not loaded.

        Args:
            required_app (Optional[str]): 'etabs' or 'sap' if a specific
                                          application module is needed.

        Raises:
            RuntimeError: If not initialized or required app module missing.
        """
        if not cls._initialized:
            logger.warning("CsiHelper not explicitly initialized. Attempting lazy initialization with default paths.")
            # Use stored paths from previous attempt or defaults
            if not cls.initialize(sap_dll=cls._sap_dll_path or DEFAULT_SAP_DLL,
                                  etabs_dll=cls._etabs_dll_path or DEFAULT_ETABS_DLL):
                 # Initialization logs the specific error
                 raise RuntimeError("CsiHelper lazy initialization failed. Check logs for details.")
            # If initialize() succeeded, cls._initialized is now True

        # Re-check after potential lazy init attempt
        if not cls._initialized:
             raise RuntimeError("CsiHelper is not initialized. Call CsiHelper.initialize() or check logs.")

        # Check if the required application module is loaded
        if required_app == 'etabs' and not cls._etabs_module:
            raise RuntimeError(f"ETABS library was not loaded during initialization. "
                               f"Check logs and path: {cls._etabs_dll_path or 'Default'}")
        if required_app == 'sap' and not cls._sap_module:
            raise RuntimeError(f"SAP2000 library was not loaded during initialization. "
                               f"Check logs and path: {cls._sap_dll_path or 'Default'}")
        if required_app and not cls._etabs_module and not cls._sap_module:
             # This case should ideally be caught by the specific checks above,
             # but added for extra safety.
             raise RuntimeError("Neither SAP nor ETABS libraries are loaded.")


    # --- Connection Management ---
    @classmethod
    def _connect(cls, app_type: str, unit: Optional[str]) -> Any:
        """
        Internal logic to connect to a running CSI application instance.

        Args:
            app_type (str): 'etabs' or 'sap'.
            unit (Optional[str]): Desired unit system key (e.g., 'N_mm_C') or None.

        Returns:
            Any: The SapModel object for the connected application.

        Raises:
            RuntimeError: If not initialized or required library missing.
            ValueError: If the specified unit is invalid.
            ConnectionError: If connection fails or already connected to the wrong app.
            Exception: For other unexpected OAPI errors.
        """
        cls._ensure_initialized(required_app=app_type) # Ensure required module is loaded

        is_etabs = app_type.lower() == 'etabs'
        app_module = cls._etabs_module if is_etabs else cls._sap_module
        unit_dict = cls._etabs_units if is_etabs else cls._sap_units
        com_prog_id = PROGID_ETABS if is_etabs else PROGID_SAP
        app_name = "ETABS" if is_etabs else "SAP2000"

        # Validate units
        units_enum = None
        if unit is not None:
            units_enum = unit_dict.get(unit)
            if units_enum is None:
                valid_units = list(unit_dict.keys())
                raise ValueError(f"Unsupported {app_name} unit: '{unit}'. Available: {valid_units}")

        # Check if already connected
        if cls._SapModel is not None:
            if cls._connected_to == app_type:
                logger.debug(f"Already connected to {app_name}. Returning existing SapModel.")
                # Set units if requested and different from current (optional optimization)
                if units_enum is not None:
                    cls._set_units_internal(app_name, unit, units_enum) # Use internal helper
                return cls._SapModel
            else:
                # Connected to the wrong application type
                msg = (f"Already connected to {cls._connected_to}. "
                       f"Please call CsiHelper.release_connection() before connecting to {app_name}.")
                logger.error(msg)
                raise ConnectionError(msg)

        # Attempt connection
        logger.info(f"Attempting to attach to running {app_name} instance...")
        try:
            # Get a reference to the running application
            try:
                # Create API helper object
                helper = app_module.cHelper(app_module.Helper())
                # Attach to running instance using the helper
                csi_object = helper.GetObject(com_prog_id)
                if csi_object is None: # Check if GetObject returned None
                    raise ConnectionError(f"helper.GetObject('{com_prog_id}') returned None. Is {app_name} running?")

            except AttributeError: # Handle cases where cHelper or Helper might not be available
                 logger.warning("cHelper method not found, attempting direct Marshal connection (may be less reliable).")
                 csi_object = Marshal.GetActiveObject(com_prog_id)

            # Cast to the specific OAPI type
            csi_oapi = app_module.cOAPI(csi_object)

            if is_etabs:
                cls._myETABSObject = csi_oapi # Store the OAPI object
            else:
                cls._mySapObject = csi_oapi # Store the OAPI object
            logger.info(f"Successfully attached to running {app_name} instance.")

            # Get the SapModel object
            SapModel = csi_oapi.SapModel
            if SapModel is None:
                 raise ConnectionError(f"Attached to {app_name}, but failed to get SapModel object.")

            # Set initial units if requested
            if units_enum is not None:
                logger.info(f"Setting initial {app_name} units to {unit}")
                ret = SapModel.SetPresentUnits(units_enum)
                if ret != 0:
                    logger.warning(f"SetPresentUnits({unit}) returned non-zero code: {ret} during initial connection.")

            cls._SapModel = SapModel # Store the connected model
            cls._connected_to = app_type # Mark connection type
            logger.info(f"{app_name} SapModel obtained and connection established.")
            return cls._SapModel

        except ConnectionError as ce: # Catch specific connection errors raised above
            logger.error(f"ConnectionError: {ce}")
            cls._reset_connection_state() # Ensure clean state on failure
            raise # Re-raise the specific error
        except Exception as e:
            # Catch COM errors (often appear as general Exceptions via pythonnet)
            # or other unexpected issues
            error_msg = f"Failed to attach to {app_name} (program may not be running or OAPI inaccessible): {e}"
            logger.error(error_msg)
            cls._reset_connection_state() # Ensure clean state on failure
            # Wrap in ConnectionError for consistency
            raise ConnectionError(error_msg) from e

    @classmethod
    def connect_to_etabs(cls, unit: Optional[str] = 'N_mm_C') -> Any:
        """
        Connects to a running ETABS instance or returns the existing connection.

        Args:
            unit (Optional[str]): Desired unit system key (e.g., 'N_mm_C').
                                  Defaults to 'N_mm_C'. Set to None to keep
                                  the current units if already connected.

        Returns:
            Any: The ETABS SapModel object.

        Raises:
            RuntimeError: If CsiHelper is not initialized or ETABS library missing.
            ValueError: If the specified unit is invalid.
            ConnectionError: If connection fails or already connected to SAP2000.
        """
        logger.debug(f"Request to connect to ETABS with unit: {unit}")
        return cls._connect(app_type='etabs', unit=unit)

    @classmethod
    def connect_to_sap(cls, unit: Optional[str] = 'N_mm_C') -> Any:
        """
        Connects to a running SAP2000 instance or returns the existing connection.

        Args:
            unit (Optional[str]): Desired unit system key (e.g., 'N_mm_C').
                                  Defaults to 'N_mm_C'. Set to None to keep
                                  the current units if already connected.

        Returns:
            Any: The SAP2000 SapModel object.

        Raises:
            RuntimeError: If CsiHelper is not initialized or SAP2000 library missing.
            ValueError: If the specified unit is invalid.
            ConnectionError: If connection fails or already connected to ETABS.
        """
        logger.debug(f"Request to connect to SAP2000 with unit: {unit}")
        return cls._connect(app_type='sap', unit=unit)

    @classmethod
    def get_active_sapmodel(cls) -> Optional[Any]:
        """
        Returns the currently active SapModel object if connected, otherwise None.
        """
        return cls._SapModel

    @classmethod
    def get_connection_type(cls) -> Optional[str]:
        """
        Returns the type of the current connection ('etabs' or 'sap'), or None.
        """
        return cls._connected_to

    @classmethod
    def _reset_connection_state(cls) -> None:
        """Internal helper to reset connection variables."""
        cls._SapModel = None
        cls._mySapObject = None
        cls._myETABSObject = None
        cls._connected_to = None

    @classmethod
    def release_connection(cls, refresh_view: bool = True) -> None:
        """
        Releases the connection to the CSI application.

        Sets internal references to the SapModel and OAPI objects to None,
        allowing Python's garbage collector and the COM subsystem to release
        the resources. Optionally refreshes the application view first.

        Args:
            refresh_view (bool): If True (default), attempts to refresh the
                                 application view before releasing.
        """
        logger.info("Releasing CSI connection...")
        if cls._SapModel is None:
            logger.info("No active CSI connection to release.")
            return

        if refresh_view:
            cls.refresh_view() # Attempt refresh before releasing

        # Set references to None. Python's GC and COM will handle actual release.
        cls._reset_connection_state()
        logger.info("CSI connection references have been released.")
        # Note: Libraries remain loaded (_initialized remains True)

    # --- Utility Methods ---
    @classmethod
    def refresh_view(cls) -> None:
        """Refreshes the ETABS/SAP2000 view if connected."""
        if cls._SapModel:
            try:
                logger.debug("Attempting to refresh view...")
                # Args: Window = 0 (refresh all), Zoom = False
                ret = cls._SapModel.View.RefreshView(0, False)
                if ret != 0:
                    logger.warning(f"SapModel.View.RefreshView() returned non-zero code: {ret}")
            except Exception as e:
                logger.warning(f"Failed to refresh view: {e}")
        else:
            logger.debug("Cannot refresh view: Not connected.")

    @classmethod
    def _set_units_internal(cls, app_name: str, unit_key: str, units_enum: Any) -> None:
        """Internal helper to set units, handling errors."""
        if not cls._SapModel:
            logger.warning(f"Cannot set {app_name} units: SapModel is not available.")
            return
        logger.debug(f"Setting {app_name} units to {unit_key}")
        try:
            ret = cls._SapModel.SetPresentUnits(units_enum)
            if ret != 0:
                logger.warning(f"SapModel.SetPresentUnits({unit_key}) returned non-zero code: {ret}")
        except Exception as e:
            logger.warning(f"Failed to set {app_name} units to {unit_key}: {e}")

    @classmethod
    def set_etabs_units(cls, unit: str = 'N_mm_C') -> None:
        """
        Sets the present units in ETABS, if connected to ETABS.

        Args:
            unit (str): The unit system key (e.g., 'N_mm_C').

        Raises:
            RuntimeError: If CsiHelper is not initialized or ETABS library missing.
            ValueError: If the specified unit key is invalid for ETABS.
            ConnectionError: If not connected to ETABS.
        """
        cls._ensure_initialized(required_app='etabs')
        if cls._connected_to != 'etabs':
            raise ConnectionError("Not connected to ETABS. Cannot set ETABS units.")

        units_enum = cls._etabs_units.get(unit)
        if units_enum is None:
             valid_units = list(cls._etabs_units.keys())
             raise ValueError(f"Invalid ETABS unit key: '{unit}'. Available: {valid_units}")

        cls._set_units_internal("ETABS", unit, units_enum)

    @classmethod
    def set_sap_units(cls, unit: str = 'N_mm_C') -> None:
        """
        Sets the present units in SAP2000, if connected to SAP2000.

        Args:
            unit (str): The unit system key (e.g., 'N_mm_C').

        Raises:
            RuntimeError: If CsiHelper is not initialized or SAP2000 library missing.
            ValueError: If the specified unit key is invalid for SAP2000.
            ConnectionError: If not connected to SAP2000.
        """
        cls._ensure_initialized(required_app='sap')
        if cls._connected_to != 'sap':
            raise ConnectionError("Not connected to SAP2000. Cannot set SAP units.")

        units_enum = cls._sap_units.get(unit)
        if units_enum is None:
            valid_units = list(cls._sap_units.keys())
            raise ValueError(f"Invalid SAP2000 unit key: '{unit}'. Available: {valid_units}")

        cls._set_units_internal("SAP2000", unit, units_enum)


# --- Helper Functions (using the CsiHelper class directly) ---

# Note: Consider moving geometry-specific helpers to a separate module if they grow.
def _get_warning_area_arguments(locations: List[float], size: float = 500.0) -> Dict[str, Any]:
    """
    Prepares coordinate data for a small triangular area used as a warning marker.

    Args:
        locations (List[float]): [x, y, z] warning location coordinates.
        size (float): Approx. base size of the triangle marker (in current model units).

    Returns:
        Dict[str, Any]: Dictionary suitable for SapModel.AreaObj.AddByCoord arguments.
    """
    # Using 'None' section property which should generally exist.
    # API will assign the actual object name.
    section_name = 'None'
    user_name = '' # Let API assign name
    num_points = 3
    csys = 'Global'

    x_loc, y_loc, z_loc = locations[0], locations[1], locations[2]

    x_coords = [x_loc, x_loc - size, x_loc + size]
    y_coords = [y_loc, y_loc - size * 2.0 , y_loc - size * 2.0]
    z_coords = [z_loc] * num_points # Flat area at the specified elevation

    # Match API argument names expected by AddByCoord
    return {
        'NumberPoints': num_points,
        'X': x_coords,
        'Y': y_coords,
        'Z': z_coords,
        'Name': '',
        'PropName': section_name or 'Default',
        'UserName': user_name,
        'CSys': csys
    }

def add_etabs_area(AddByCoord_args: Dict[str, Any]) -> Optional[str]:
    """
    Adds a area object in ETABS at the specified coordinates.

    Connects to ETABS using CsiHelper if not already connected. 

    Args:
        AddByCoord_args (Dict[str, Any]): Dictionary suitable for SapModel.AreaObj.AddByCoord arguments.

    Returns:
        Optional[str]: The name of the created area object, or None on failure.
    """
    logger.info(f"Attempting to add ETABS area at {AddByCoord_args}")
    try:
        # Ensure connected to ETABS. Use unit=None to
        SapModel = CsiHelper.connect_to_etabs(unit=None)
        if not SapModel:
            logger.warning("Failed to connect to ETABS. Cannot add area.")
            return None

        ret = SapModel.AreaObj.AddByCoord(
            **AddByCoord_args
        )

        # Check return code
        if ret[0] != 0:
            logger.error(f"Failed adding ETABS area object at {AddByCoord_args}; ETABS API returned code {ret[0]}")
            return None

        # Get the name of the created area object
        area_name = str(ret[4])
        logger.info(f"Successfully added ETABS area object '{area_name}' at {AddByCoord_args}")

        return area_name # Return the name assigned by ETABS
    except (RuntimeError, ConnectionError, ValueError) as e:
        # Catch errors from CsiHelper or value errors (e.g., bad coords if validation added)
        logger.error(f"CSI interaction error during add_area: {e}")
        return None
    except Exception as e:
        # Catch unexpected errors (e.g., COM errors from API calls)
        logger.exception(f"An unexpected error occurred during add_area:") # Includes traceback
        return None

def add_etabs_warning_mark(
        location: List[float],
        size: float = 500.0,
        group_name: Optional[str] = 'Warnings'
    ) -> Optional[str]:
    """
    Adds warning marks in ETABS at the specified locations.

    Connects to ETABS using CsiHelper if not already connected. Creates the
    specified group if it doesn't exist and assigns the new area to it.

    Args:
        location (List[float]): [x, y, z] warning location coordinates.
        size (float): Approx. base size of the triangle marker (in current model units).
        group_name (str): Name of the group to create (if needed) and assign the area to.

    Returns:
        Optional[str]: The name of the created area object, or None on failure.
    """
    logger.info(f"Attempting to add ETABS warning marks at {location}")
    try:
        # Ensure connected to ETABS. Use unit=None to avoid changing current units.
        SapModel = CsiHelper.connect_to_etabs(unit=None)
        if not SapModel:
            logger.warning("Failed to connect to ETABS. Cannot add warning marks.")
            return None

        # Prepare the area arguments
        area_args = _get_warning_area_arguments(location, size)

        # Add the area
        area_name = add_etabs_area(area_args)
        if not area_name:
            logger.error("Failed to add ETABS area object. Cannot assign to group.")
            return None

        if group_name:
            # Assign the area to the group
            ret = SapModel.AreaObj.SetGroupAssign(area_name, group_name)
            if ret!= 0:  # Check return code
                logger.error(f"Failed to assign area '{area_name}' to group '{group_name}'; ETABS API returned code {ret}")
                return None

        logger.info(f"Successfully added ETABS warning mark at {location}")
        return area_name # Return the name assigned by ETABS
    except (RuntimeError, ConnectionError, ValueError) as e:    # Catch errors from CsiHelper or value errors (e.g., bad coords if validation added)
        logger.error(f"CSI interaction error during add_etabs_warning_mark: {e}")
        return None
    except Exception as e:
        # Catch unexpected errors (e.g., COM errors from API calls)     
        logger.exception(f"An unexpected error occurred during add_etabs_warning_mark:") # Includes traceback  
        return None





def get_etabs_groups() -> Optional[List[str]]:
    """
    Retrieves a list of all group names defined in the current ETABS model.

    Connects to ETABS using CsiHelper if not already connected.

    Returns:
        Optional[List[str]]: A list of group names, or None on failure.
    """
    logger.debug("Attempting to retrieve ETABS groups.")
    try:
        SapModel = CsiHelper.connect_to_etabs(unit=None)

        etabs_groups = {
            'NumberNames': 0,
            'MyName': []
        }

        ret = SapModel.GroupDef.GetNameList(**etabs_groups)

        if ret[0] != 0:
            logger.error(f'Failed reading group names; ETABS API returned code {ret[0]}')
            return None

 
        actual_group_names = list(ret[2])
        logger.info(f"Successfully retrieved {len(actual_group_names)} ETABS groups.")
        logger.debug(f"Retrieved groups: {actual_group_names}")
        return actual_group_names

    except (RuntimeError, ConnectionError) as e:
        logger.error(f"CSI interaction error during get_etabs_groups: {e}")
        return None
    except Exception as e:
        logger.exception(f"An unexpected error occurred during get_etabs_groups:")
        return None


def create_etabs_group(group_name: str) -> Optional[str]:
    """
    Creates a group in ETABS if it doesn't already exist.

    Connects to ETABS using CsiHelper if not already connected.

    Args:
        group_name (str): The name of the group to create. Cannot be empty.

    Returns:
        Optional[str]: The group name if successfully created or already exists,
                       otherwise None.
    """
    if not isinstance(group_name, str) or not group_name.strip():
        logger.error("Group name must be a non-empty string.")
        return None
    group_name = group_name.strip() # Use trimmed name

    logger.debug(f"Request to ensure ETABS group '{group_name}' exists.")
    try:
        SapModel = CsiHelper.connect_to_etabs(unit=None)

        # Check if group already exists first
        etabs_groups_names = get_etabs_groups()
        if etabs_groups_names is None:
            # Error already logged by get_etabs_groups
            logger.error(f"Failed to retrieve existing groups. Cannot ensure group '{group_name}' exists.")
            return None

        if group_name in etabs_groups_names:
            logger.debug(f"Group '{group_name}' already exists.")
            return group_name # Group exists, success.
        else:
            # Group does not exist, create it
            logger.info(f"Creating ETABS group: '{group_name}'")

            SetGroup = {
                'Name' : group_name,
                'color' : -1,
                'SpecifiedForSelection' : True,
                'SpecifiedForSectionCutDefinition' : False,
                'SpecifiedForSteelDesign' : False,
                'SpecifiedForConcreteDesign' : False,
                'SpecifiedForAluminumDesign' : False,
                'SpecifiedForStaticNLActiveStage' : False,
                'SpecifiedForAutoSeismicOutput' : False,
                'SpecifiedForAutoWindOutput' : False,
                'SpecifiedForMassAndWeight' : False,
                'SpecifiedForSteelJoistDesign' : False,
                'SpecifiedForWallDesign' : False,
                'SpecifiedForBasePlateDesign' : False,
                'SpecifiedForConnectionDesign' : False,
            }
            ret = SapModel.GroupDef.SetGroup_1(**SetGroup)
            if ret != 0:
                logger.error(f"Failed creating group '{group_name}'; ETABS API returned code {ret}")
                return None

            logger.info(f"Group '{group_name}' created successfully.")
            return group_name # Return group name on successful creation

    except (RuntimeError, ConnectionError) as e:
        logger.error(f"CSI interaction error during create_etabs_group for '{group_name}': {e}")
        return None
    except Exception as e:
        logger.exception(f"An unexpected error occurred during create_etabs_group for '{group_name}':")
        return None



''' how to use
(Optional but Recommended): Call CsiHelper.initialize() early in your script if you know the DLL paths and want to control when loading occurs.

import mat_ceng.csi as csi
# Optional: Specify paths if different from defaults
# success = csi.CsiHelper.initialize(sap_dll="path/to/sap.dll", etabs_dll="path/to/etabs.dll")
success = csi.CsiHelper.initialize()
if not success:
    print("Failed to initialize CSI Helper. Exiting.")
    exit()



Use the helper functions or class methods directly:
# Using helper function
area_name = csi.add_area([1000, 2000, 0])

# Or using class methods directly
try:
    sap_model = csi.CsiHelper.connect_to_sap(unit='kN_m_C')
    if sap_model:
        # Do something with sap_model
        print("Connected to SAP2000")
        csi.CsiHelper.release_connection()
except (RuntimeError, ConnectionError, ValueError) as e:
    print(f"Error connecting to SAP2000: {e}")

'''