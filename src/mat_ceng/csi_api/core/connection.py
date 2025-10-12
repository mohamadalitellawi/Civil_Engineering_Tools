# src/csi_api/core/connection.py

import os
import subprocess
import time
from .utils import validate_software_path
from ..exceptions import ConnectionError
from enum import Enum

def connect_to_csi_api(prog_id, dll_path = None, exe_path=None, attach_to_existing=True, timeout=10):
    """
    Connect to CSI software via COM.
    """
    try:
        import clr
        clr.AddReference("System.Runtime.InteropServices")
        from System.Runtime.InteropServices import Marshal
        clr.AddReference(dll_path)
        import ETABSv1 as etabs

        #create API helper object
        helper = etabs.cHelper(etabs.Helper())

        #clr.AddReference("System")
        #from System import Type, Activator
    except ImportError as e:
        raise ConnectionError("pythonnet not installed or .NET not available") from e

    if attach_to_existing:
        try:
            myETABSObject = etabs.cOAPI(helper.GetObject("CSI.ETABS.API.ETABSObject"))
            SapModel = etabs.cSapModel(myETABSObject.SapModel)
            if myETABSObject:
                return myETABSObject, SapModel, etabs
        except Exception as e:
            raise ConnectionError(f"No running instance of the program found or failed to attach.: {e}") from e

    if exe_path:
        exe_path = validate_software_path(exe_path)
        #subprocess.Popen([exe_path])
        #time.sleep(timeout)

        try:
            myETABSObject = etabs.cOAPI(helper.CreateObject(exe_path))
            SapModel = etabs.cSapModel(myETABSObject.SapModel)
            ret = myETABSObject.ApplicationStart()
            return myETABSObject, SapModel, etabs
        except Exception as e:
            raise ConnectionError(f"Failed to connect after launching: {e}") from e
    else:
        raise ConnectionError("exe_path required when attach_to_existing=False")
