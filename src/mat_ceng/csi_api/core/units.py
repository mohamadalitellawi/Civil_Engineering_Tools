# src/csi_api/core/units.py
from ..exceptions import ModelError
# ETABS unit constants (from CSI API documentation)
FORCE_UNITS = {
    0: "NotApplicable",
    1: "lb",
    2: "kip",
    3: "N",
    4: "kN",
    5: "kgf",
    6: "tonf",  # metric ton
}

LENGTH_UNITS = {
    0: "NotApplicable",
    1: "inch",
    2: "ft",
    3: "micron",
    4: "mm",
    5: "cm",
    6: "m",
}

TEMPERATURE_UNITS = {
    0: "NotApplicable",
    1: "F",
    2: "C",
}


# Map to moment units (force × length)
def get_moment_unit(force_unit_id, length_unit_id):
    force_label = FORCE_UNITS.get(force_unit_id, "force")
    length_label = LENGTH_UNITS.get(length_unit_id, "length")
    return f"{force_label}{length_label}"

def detect_units_from_etabs(sap_model, etabs_object, etabs_dll_lib):
    """
    Detect force and length units from ETABS SapModel.
    
    Returns:
        dict with keys: 'force', 'length', 'moment'
    """
    try:
        # Get units: [force, length, temperature, ...]
        forceUnits = etabs_dll_lib.eForce.NotApplicable
        lengthUnits = etabs_dll_lib.eLength.NotApplicable
        temperatureUnits = etabs_dll_lib.eTemperature.NotApplicable
        units = sap_model.GetPresentUnits_2(forceUnits, lengthUnits, temperatureUnits)
        if units[0] != 0:
            raise RuntimeError("Failed to get units from model")

        force_id = units[1]   # index 1 = force
        length_id = units[2]  # index 2 = length
        temperature_id = units[3]

        force_label = FORCE_UNITS.get(force_id, f"force_{force_id}")
        length_label = LENGTH_UNITS.get(length_id, f"length_{length_id}")
        temperature_label = TEMPERATURE_UNITS.get(temperature_id, f"temperature_{temperature_id}")
        moment_label = get_moment_unit(force_id, length_id)

        return {
            "force": force_label,
            "length": length_label,
            "moment": moment_label,
            "temperature": temperature_label
        }
    except Exception as e:
        raise ModelError(f"Failed to get model units: {e}") from e
        # Fallback to kN, m, kNm if detection fails
        return {
            "force": "kN",
            "length": "m",
            "moment": "kNm",
            "temperature": "C"
        }
    
