import clr
# Attempt to add references early, handle potential errors during import
try:
    clr.AddReference("System.Runtime.InteropServices")
    # These imports might fail if the DLLs are not found,
    # CsiHelper.__init__ will handle the actual loading and error reporting.
    # We import them here to make the types available for type hinting if desired.
    # clr.AddReference(R'C:\Program Files\Computers and Structures\SAP2000 26\SAP2000v1.dll') # Path handled in __init__
    # clr.AddReference(R'C:\Program Files\Computers and Structures\ETABS 22\ETABSv1.dll') # Path handled in __init__
    # import SAP2000v1 as sap_module # Alias to avoid conflict
    # import ETABSv1 as etabs_module # Alias to avoid conflict
except Exception as e:
    print(f"Warning: Failed to add initial CLR references during import: {e}")
    # sap_module = None
    # etabs_module = None

from System.Runtime.InteropServices import Marshal # Keep this import


class CsiHelper:
    """
    Manage Csi Models and Objects using the Singleton pattern.
    Ensures only one instance manages the connection.
    """
    _instance = None
    _initialized = False # Flag to ensure __init__ runs only once

    def __new__(cls, *args, **kwargs):
        if cls._instance is None:
            print("Creating new CsiHelper instance") # For debugging
            cls._instance = super().__new__(cls)
            # Initialize instance attributes that should exist on the single instance
            cls._instance._sap = None
            cls._instance._etabs = None
            cls._instance._SapModel = None
            cls._instance._mySapObject = None
            cls._instance._myETABSObject = None
            cls._instance._etabs_units = {}
            cls._instance._sap_units = {}
            cls._instance._connected_to = None # Track if connected to 'etabs' or 'sap'
            cls._instance._initialized = False # Ensure __init__ runs for the new instance
        else:
            print("Returning existing CsiHelper instance") # For debugging
        return cls._instance

    def __init__(self,
                 sap_dll=R'C:\Program Files\Computers and Structures\SAP2000 26\SAP2000v1.dll',
                 etabs_dll=R'C:\Program Files\Computers and Structures\ETABS 22\ETABSv1.dll'):
        """
        Initializes the CsiHelper instance (only runs once).
        Loads necessary libraries and sets up unit dictionaries.
        """
        if self._initialized: # Check the instance's flag
            # print("CsiHelper already initialized, skipping.") # For debugging
            return
        print("Initializing CsiHelper...") # For debugging

        # Perform the actual initialization logic (imports, etc.)
        try:
            # Add references if not already added (though AddReference usually handles this)
            try: clr.AddReference(sap_dll)
            except Exception as e: print(f"Warning: Could not add reference {sap_dll}: {e}")
            import SAP2000v1 as sap

            try: clr.AddReference(etabs_dll)
            except Exception as e: print(f"Warning: Could not add reference {etabs_dll}: {e}")
            import ETABSv1 as etabs

            self._sap = sap
            self._etabs = etabs

            # Initialize unit dictionaries *on the instance*
            self._etabs_units = {
                'N_mm_C' : self._etabs.eUnits.N_mm_C,
                'kN_m_C' : self._etabs.eUnits.kN_m_C,
            }
            self._sap_units = {
                'N_mm_C': self._sap.eUnits.N_mm_C,
                'kN_m_C': self._sap.eUnits.kN_m_C,
            }

            self._initialized = True # Mark this instance as initialized
            print("CsiHelper initialization complete.") # For debugging
        except ImportError as e:
            print(f"ERROR: Failed to import CSI libraries: {e}")
            print(f"Ensure DLL paths are correct:\n SAP: {sap_dll}\n ETABS: {etabs_dll}")
            # Instance remains uninitialized. Subsequent calls might fail.
            # Consider raising a more specific error if needed.
            # self._initialized remains False
        except Exception as e:
            print(f"ERROR: An unexpected error occurred during CsiHelper initialization: {e}")
            # self._initialized remains False

    def _check_initialized(self):
        """Raises RuntimeError if the helper wasn't initialized successfully."""
        if not self._initialized:
            raise RuntimeError("CsiHelper is not initialized. Check logs for import or setup errors.")
        if not self._sap or not self._etabs:
             raise RuntimeError("CSI libraries (SAP/ETABS) not loaded during initialization.")

    def _connect(self, app_type='etabs', unit='N_mm_C'):
        """Internal connection logic."""
        self._check_initialized()

        is_etabs = app_type.lower() == 'etabs'
        app_module = self._etabs if is_etabs else self._sap
        unit_dict = self._etabs_units if is_etabs else self._sap_units
        com_prog_id = "CSI.ETABS.API.ETABSObject" if is_etabs else "CSI.SAP2000.API.SapObject"
        app_name = "ETABS" if is_etabs else "SAP2000"

        units = unit_dict.get(unit)
        if units is None and unit is not None:
            raise ValueError(f"Unsupported {app_name} unit: {unit}. Available: {list(unit_dict.keys())}")

        # Check if already connected to the *correct* application
        if self._SapModel is not None:
            if self._connected_to == app_type:
                # print(f"{app_name} SapModel already exists.") # Debugging
                if units is not None:
                    # print(f"Setting {app_name} units to {unit}") # Debugging
                    try:
                        ret = self._SapModel.SetPresentUnits(units)
                        if ret != 0: print(f"Warning: SetPresentUnits returned {ret}")
                    except Exception as e:
                        print(f"Warning: Failed to set units for existing {app_name} connection: {e}")
                return self._SapModel
            else:
                # Connected to the wrong application type
                raise ConnectionError(f"Already connected to {self._connected_to}. Please release connection before connecting to {app_name}.")

        # Attempt connection
        print(f"Attempting to connect to {app_name}...") # Debugging
        try:
            # Create API helper object
            helper = app_module.cHelper(app_module.Helper())
            # Attach to running instance
            csi_object = app_module.cOAPI(helper.GetObject(com_prog_id))

            if is_etabs:
                self._myETABSObject = csi_object
            else:
                self._mySapObject = csi_object
            print(f"Attached to running {app_name} instance.") # Debugging

            # Create SapModel object
            SapModel = app_module.cSapModel(csi_object.SapModel)
            if units is not None:
                print(f"Setting initial {app_name} units to {unit}") # Debugging
                ret = SapModel.SetPresentUnits(units)
                if ret != 0: print(f"Warning: SetPresentUnits (initial) returned {ret}")

            self._SapModel = SapModel # Store the connected model
            self._connected_to = app_type # Mark connection type
            print(f"{app_name} SapModel created and stored.") # Debugging
            return self._SapModel

        except Exception as e:
            error_msg = f"No running {app_name} instance found or failed to attach: {e}"
            print(error_msg) # Debugging
            # Ensure state is clean if connection failed mid-way
            self._SapModel = None
            self._connected_to = None
            if is_etabs: self._myETABSObject = None
            else: self._mySapObject = None
            raise ConnectionError(error_msg) from e


    def connect_to_etabs(self, unit = 'N_mm_C'):
        """
        Connect To Running Etabs Instance or return existing ETABS connection.
        Args:
            unit (str): Desired unit system ('N_mm_C', 'kN_m_C', None to keep existing).
        Returns: Etabs SapModel object
        Raises: RuntimeError, ValueError, ConnectionError
        """
        return self._connect(app_type='etabs', unit=unit)

    def connect_to_sap(self, unit = 'N_mm_C'):
        """
        Connect To Running SAP2000 Instance or return existing SAP2000 connection.
        Args:
            unit (str): Desired unit system ('N_mm_C', 'kN_m_C', None to keep existing).
        Returns: SAP2000 SapModel object
        Raises: RuntimeError, ValueError, ConnectionError
        """
        return self._connect(app_type='sap', unit=unit)

    def get_active_sapmodel(self):
        """Returns the currently active SapModel, regardless of type, or None."""
        return self._SapModel

    def refresh_view(self):
        """Refreshes the ETABS/SAP2000 view if connected."""
        if self._SapModel:
            try:
                # print("Refreshing view...") # Debugging
                ret = self._SapModel.View.RefreshView(0, False)
                # if ret != 0: print(f"Warning: RefreshView returned {ret}")
            except Exception as e:
                print(f"Warning: Failed to refresh view: {e}")
        # else:
            # print("Cannot refresh view: Not connected.") # Debugging

    def set_etabs_units(self, unit = 'N_mm_C'):
        """Sets ETABS units if connected to ETABS."""
        self._check_initialized()
        if self._connected_to != 'etabs':
            print("Warning: Not connected to ETABS. Cannot set ETABS units.")
            return
        if not self._SapModel:
             print("Warning: SapModel is None. Cannot set ETABS units.")
             return

        units = self._etabs_units.get(unit)
        if units is None: raise ValueError(f"Invalid ETABS unit: {unit}")

        print(f"Setting ETABS units to {unit}") # Debugging
        try:
            ret = self._SapModel.SetPresentUnits(units)
            if ret != 0: print(f"Warning: SetPresentUnits returned {ret}")
        except Exception as e:
            print(f"Warning: Failed to set ETABS units: {e}")


    def set_sap_units(self, unit='N_mm_C'):
        """Sets SAP2000 units if connected to SAP2000."""
        self._check_initialized()
        if self._connected_to != 'sap':
            print("Warning: Not connected to SAP2000. Cannot set SAP units.")
            return
        if not self._SapModel:
             print("Warning: SapModel is None. Cannot set SAP units.")
             return

        units = self._sap_units.get(unit)
        if units is None: raise ValueError(f"Invalid SAP2000 unit: {unit}")

        print(f"Setting SAP2000 units to {unit}") # Debugging
        try:
            ret = self._SapModel.SetPresentUnits(units)
            if ret != 0: print(f"Warning: SetPresentUnits returned {ret}")
        except Exception as e:
            print(f"Warning: Failed to set SAP units: {e}")

    def release_csi_models(self, refresh_view = True):
        """
        Cleans and releases current CSI objects (sets internal references to None).
        Optionally refreshes the view before releasing.
        """
        print("Releasing CSI models...") # Debugging
        if refresh_view:
            self.refresh_view()

        # Release COM objects by setting references to None.
        # Garbage collection should handle the actual release.
        self._SapModel = None
        self._mySapObject = None
        self._myETABSObject = None
        self._connected_to = None # Reset connection type
        print("CSI model references released (set to None).") # Debugging


# --- Global Helper Instance ---
# Instantiate the singleton. Errors during init are caught and printed.
# Functions below should check if csi_helper_instance is valid.
try:
    csi_helper_instance = CsiHelper()
except Exception as e:
    # Catch potential errors during the *first* instantiation/initialization
    print(f"FATAL: Failed to create CsiHelper instance during module load: {e}")
    csi_helper_instance = None

# --- Helper Functions (using the singleton instance) ---

def _get_warning_area_coordinates(coordinates, size = 500.0):
    """Prepares coordinate data for AddByCoord."""
    # (No changes needed in this function itself)
    name = '' # API will assign name
    section_name = 'None' # Use 'None' section
    slab_pnt_count = 3

    x_loc = coordinates[0]
    y_loc = coordinates[1]
    z_loc = coordinates[2]

    # Define a small triangular area for warning marker
    x_left = x_loc - size
    x_right = x_loc + size
    y_bottom = y_loc - size * 1.732 # Approx height for equilateral triangle base 'size*2'

    x = [x_loc, x_left, x_right]
    y = [y_loc, y_bottom, y_bottom]
    z = [z_loc] * slab_pnt_count # Same Z coordinate

    AddByCoordArgs = {
        'NumberPoints': slab_pnt_count,
        'X': x,
        'Y': y,
        'Z': z,
        'PropName': section_name,
        'UserName': name, # Let ETABS assign name based on internal counter
        'CSys': 'Global'
    }
    return AddByCoordArgs


def add_area(coords, group_name = 'Warnings'):
    """
    Adds a warning area object in ETABS at the specified coordinates.
    Connects to ETABS if not already connected.
    Args:
        coords (list/tuple): [x, y, z] coordinates for the area center.
        group_name (str): Name of the group to create (if needed) and assign the area to.
    Returns:
        str: The name of the created area object, or None on failure.
    """
    if not csi_helper_instance or not csi_helper_instance._initialized:
        print("ERROR: CsiHelper not available or not initialized. Cannot add area.")
        return None
    try:
        # Ensure connected to ETABS, use None for unit to avoid changing it
        SapModel = csi_helper_instance.connect_to_etabs(unit=None)
        if not SapModel: return None # Should not happen if connect raises errors

        coord_data = _get_warning_area_coordinates(coords)
        # AddByCoord returns: [ret_code, Name, ret_val]
        # ret_val seems deprecated or unused based on docs for AddByCoord
        ret_code, area_name_assigned, _ = SapModel.AreaObj.AddByCoord(
            coord_data['NumberPoints'], coord_data['X'], coord_data['Y'], coord_data['Z'],
            coord_data['PropName'], coord_data['UserName'], coord_data['CSys']
        )

        if ret_code != 0:
            print(f'ERROR: Failed adding area object; ETABS CODE {ret_code}')
            return None

        area_name = str(area_name_assigned)
        print(f"Successfully added area object: {area_name}") # Debugging

        if group_name:
            # Ensure group exists before assigning
            created_group = create_etabs_group(group_name) # Use the refactored function
            if created_group:
                ret = SapModel.AreaObj.SetGroupAssign(area_name, group_name)
                if ret == 0:
                    print(f"Assigned area {area_name} to group {group_name}") # Debugging
                else:
                     print(f"Warning: Failed to assign area {area_name} to group {group_name}. Code: {ret}")
            else:
                print(f"Warning: Could not create/find group '{group_name}'. Area '{area_name}' not assigned to group.")

        return area_name
    except ConnectionError as e:
        print(f"ERROR: Connection failed during add_area: {e}")
        return None
    except Exception as e:
        print(f"ERROR: An unexpected error occurred during add_area: {e}")
        # Potentially log traceback here
        return None


def get_etabs_groups():
    """
    Retrieves a list of all group names defined in the current ETABS model.
    Connects to ETABS if not already connected.
    Returns:
        list[str]: A list of group names, or None on failure.
    """
    if not csi_helper_instance or not csi_helper_instance._initialized:
        print("ERROR: CsiHelper not available or not initialized. Cannot get groups.")
        return None
    try:
        # Ensure connected to ETABS, use None for unit to avoid changing it
        SapModel = csi_helper_instance.connect_to_etabs(unit=None)
        if not SapModel: return None

        # GetNameList requires variables to be passed for output
        num_names = 0
        group_names_tuple = () # API expects a tuple reference for output
        ret_code, num_names_out, group_names_out = SapModel.GroupDef.GetNameList(num_names, group_names_tuple)

        if ret_code != 0:
            print(f'ERROR: Failed reading groups names; ETABS CODE {ret_code}')
            return None

        # Convert the returned tuple (or array) to a list
        actual_group_names = list(group_names_out)
        # print(f"Retrieved groups: {actual_group_names}") # Debugging
        return actual_group_names
    except ConnectionError as e:
        print(f"ERROR: Connection failed during get_etabs_groups: {e}")
        return None
    except Exception as e:
        print(f"ERROR: An unexpected error occurred during get_etabs_groups: {e}")
        return None


def create_etabs_group(group_name):
    """
    Creates a group in ETABS if it doesn't already exist.
    Connects to ETABS if not already connected.
    Args:
        group_name (str): The name of the group to create.
    Returns:
        str: The group name if successfully created or already exists, otherwise None.
    """
    if not csi_helper_instance or not csi_helper_instance._initialized:
        print("ERROR: CsiHelper not available or not initialized. Cannot create group.")
        return None
    if not group_name:
        print("ERROR: Group name cannot be empty.")
        return None

    try:
        # Ensure connected to ETABS, use None for unit to avoid changing it
        SapModel = csi_helper_instance.connect_to_etabs(unit=None)
        if not SapModel: return None

        etabs_groups_names = get_etabs_groups() # Use the refactored function
        if etabs_groups_names is None:
            # Error message already printed by get_etabs_groups
            print("ERROR: Failed to retrieve existing groups. Cannot create new group.")
            return None

        if group_name not in etabs_groups_names:
            print(f"Creating ETABS group: {group_name}") # Debugging
            # SetGroup_1 expects individual arguments
            color = 10 # Use a distinct color (e.g., Yellow) for warnings, default is -1 (black/white)
            SpecifiedForSelection = True
            # Set other flags to False as per original code
            ret = SapModel.GroupDef.SetGroup_1(
                group_name, color, SpecifiedForSelection,
                False, False, False, False, False, False, False, False, False, False, False, False
            )

            if ret != 0:
                print(f'ERROR: Failed creating group "{group_name}"; ETABS CODE {ret}')
                return None
            print(f"Group '{group_name}' created successfully.") # Debugging
        # else:
            # print(f"Group '{group_name}' already exists.") # Debugging

        return group_name # Return group name on success or if already exists
    except ConnectionError as e:
        print(f"ERROR: Connection failed during create_etabs_group: {e}")
        return None
    except Exception as e:
        print(f"ERROR: An unexpected error occurred during create_etabs_group: {e}")
        return None

