# src/csi_api/core/units.py
from ..exceptions import ModelError
from enum import Enum



def get_force_units_enum (etabs_dll_lib):
    class ForceUnit(Enum):
        NotApplicable = etabs_dll_lib.eForce.NotApplicable 
        lb = etabs_dll_lib.eForce.lb
        kip = etabs_dll_lib.eForce.kip
        N = etabs_dll_lib.eForce.N
        kN = etabs_dll_lib.eForce.kN
        kgf = etabs_dll_lib.eForce.kgf
        tonf = etabs_dll_lib.eForce.tonf
    return ForceUnit

def get_length_units_enum (etabs_dll_lib):
    class LengthUnit(Enum):
        NotApplicable = etabs_dll_lib.eLength.NotApplicable 
        inch = etabs_dll_lib.eLength.inch
        ft = etabs_dll_lib.eLength.ft
        micron = etabs_dll_lib.eLength.micron
        mm = etabs_dll_lib.eLength.mm
        cm = etabs_dll_lib.eLength.cm
        m = etabs_dll_lib.eLength.m
    return LengthUnit

def get_temperature_units_enum (etabs_dll_lib):
    class TemperatureUnit(Enum):
        NotApplicable = etabs_dll_lib.eTemperature.NotApplicable 
        F = etabs_dll_lib.eTemperature.F
        C = etabs_dll_lib.eTemperature.C
    return TemperatureUnit


def detect_units_from_etabs(sap_model, etabs_dll_lib):
    """
    Detect force and length units from ETABS SapModel.
    
    Returns:
        dict with keys: 'force', 'length', 'temperature'
    """
    try:
        # Get units: [force, length, temperature, ...]
        forceUnits = etabs_dll_lib.eForce.NotApplicable
        lengthUnits = etabs_dll_lib.eLength.NotApplicable
        temperatureUnits = etabs_dll_lib.eTemperature.NotApplicable
        units = sap_model.GetPresentUnits_2(forceUnits, lengthUnits, temperatureUnits)

        if units[0] != 0:
            raise RuntimeError("Failed to get units from model")
        units_names = [str(x) for x in units[1:]]

        force_label = units_names[0]
        length_label = units_names[1]
        temperature_label = units_names[2]
        # moment_label = get_moment_unit(force_id, length_id)

        return {
            "force": force_label,
            "length": length_label,
            "temperature": temperature_label,
        }
    
    except Exception as e:
        raise ModelError(f"Failed to get model units: {e}") from e


    
