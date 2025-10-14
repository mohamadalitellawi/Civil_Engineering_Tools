"""
Utility helper functions for CSI Toolkit.

Common functions used across different modules.
"""

from typing import Dict, Any, List, Tuple
from pathlib import Path
import json
from loguru import logger


# ==================== UNIT CONVERSIONS ====================

# ETABS/SAP2000 unit codes
FORCE_UNITS = {
    'lb': 1,
    'kip': 2,
    'N': 3,
    'kN': 4,
    'kgf': 5,
    'tonf': 6
}

LENGTH_UNITS = {
    'in': 1,
    'ft': 2,
    'micron': 3,
    'mm': 4,
    'cm': 5,
    'm': 6
}


def get_unit_codes(force_unit: str, length_unit: str) -> Tuple[int, int]:
    """
    Get unit codes for CSI API.
    
    Args:
        force_unit: Force unit name (e.g., 'kN', 'kip')
        length_unit: Length unit name (e.g., 'm', 'ft')
    
    Returns:
        Tuple of (force_code, length_code)
    
    Example:
        >>> force_code, length_code = get_unit_codes('kN', 'm')
    """
    force_code = FORCE_UNITS.get(force_unit)
    length_code = LENGTH_UNITS.get(length_unit)
    
    if force_code is None:
        raise ValueError(
            f"Unknown force unit: {force_unit}. "
            f"Valid options: {list(FORCE_UNITS.keys())}"
        )
    
    if length_code is None:
        raise ValueError(
            f"Unknown length unit: {length_unit}. "
            f"Valid options: {list(LENGTH_UNITS.keys())}"
        )
    
    return force_code, length_code


# ==================== FILE OPERATIONS ====================

def ensure_file_extension(file_path: str, extension: str) -> str:
    """
    Ensure file has the correct extension.
    
    Args:
        file_path: Original file path
        extension: Required extension (with or without dot)
    
    Returns:
        File path with correct extension
    """
    if not extension.startswith('.'):
        extension = f'.{extension}'
    
    path = Path(file_path)
    if path.suffix.lower() != extension.lower():
        return str(path.with_suffix(extension))
    return file_path


def validate_file_exists(file_path: str) -> Path:
    """
    Validate that a file exists.
    
    Args:
        file_path: Path to file
    
    Returns:
        Path object
    
    Raises:
        FileNotFoundError: If file doesn't exist
    """
    path = Path(file_path)
    if not path.exists():
        raise FileNotFoundError(f"File not found: {file_path}")
    return path


def create_directory(dir_path: str) -> Path:
    """
    Create directory if it doesn't exist.
    
    Args:
        dir_path: Directory path
    
    Returns:
        Path object
    """
    path = Path(dir_path)
    path.mkdir(parents=True, exist_ok=True)
    logger.debug(f"Ensured directory exists: {path}")
    return path


# ==================== DATA STRUCTURES ====================

def parse_csi_array_result(result: tuple, field_names: List[str]) -> List[Dict[str, Any]]:
    """
    Parse CSI API array result into list of dictionaries.
    
    Many CSI API functions return results as tuples of arrays.
    This helper converts them to a more Pythonic format.
    
    Args:
        result: Tuple returned from CSI API (count, array1, array2, ...)
        field_names: Names for each field
    
    Returns:
        List of dictionaries with named fields
    
    Example:
        >>> result = (2, ['P1', 'P2'], [0.0, 1.0], [0.0, 2.0])
        >>> data = parse_csi_array_result(result, ['Name', 'X', 'Y'])
        >>> # Returns: [{'Name': 'P1', 'X': 0.0, 'Y': 0.0}, ...]
    """
    count = result[0]
    if count == 0:
        return []
    
    data = []
    for i in range(count):
        item = {}
        for j, field_name in enumerate(field_names):
            # Skip the count (first element)
            item[field_name] = result[j + 1][i]
        data.append(item)
    
    return data


def dict_to_json_file(data: Dict[str, Any], file_path: str, indent: int = 2) -> None:
    """
    Save dictionary to JSON file.
    
    Args:
        data: Dictionary to save
        file_path: Output file path
        indent: JSON indentation
    """
    with open(file_path, 'w') as f:
        json.dump(data, f, indent=indent)
    logger.info(f"Saved data to {file_path}")


def json_file_to_dict(file_path: str) -> Dict[str, Any]:
    """
    Load dictionary from JSON file.
    
    Args:
        file_path: JSON file path
    
    Returns:
        Dictionary with data
    """
    with open(file_path, 'r') as f:
        data = json.load(f)
    logger.info(f"Loaded data from {file_path}")
    return data


# ==================== COORDINATE OPERATIONS ====================

def calculate_distance_3d(
    x1: float, y1: float, z1: float,
    x2: float, y2: float, z2: float
) -> float:
    """
    Calculate 3D distance between two points.
    
    Args:
        x1, y1, z1: Coordinates of first point
        x2, y2, z2: Coordinates of second point
    
    Returns:
        Distance
    """
    return ((x2 - x1)**2 + (y2 - y1)**2 + (z2 - z1)**2)**0.5


def grid_points_rectangular(
    x_start: float,
    x_end: float,
    x_spacing: float,
    y_start: float,
    y_end: float,
    y_spacing: float,
    z: float = 0.0
) -> List[Tuple[float, float, float]]:
    """
    Generate rectangular grid of points.
    
    Args:
        x_start, x_end: X coordinate range
        x_spacing: Spacing in X direction
        y_start, y_end: Y coordinate range
        y_spacing: Spacing in Y direction
        z: Z coordinate (constant)
    
    Returns:
        List of (x, y, z) tuples
    """
    import numpy as np
    
    x_coords = np.arange(x_start, x_end + x_spacing/2, x_spacing)
    y_coords = np.arange(y_start, y_end + y_spacing/2, y_spacing)
    
    points = []
    for x in x_coords:
        for y in y_coords:
            points.append((float(x), float(y), z))
    
    return points


# ==================== RESULT PROCESSING ====================

def find_max_value_in_results(
    data: List[Dict[str, Any]],
    value_field: str
) -> Dict[str, Any]:
    """
    Find entry with maximum value for a specific field.
    
    Args:
        data: List of result dictionaries
        value_field: Field name to maximize
    
    Returns:
        Dictionary entry with max value
    """
    if not data:
        return {}
    
    return max(data, key=lambda x: abs(x.get(value_field, 0)))


def filter_results_by_load_case(
    data: List[Dict[str, Any]],
    load_case: str,
    case_field: str = 'LoadCase'
) -> List[Dict[str, Any]]:
    """
    Filter results for specific load case.
    
    Args:
        data: List of result dictionaries
        load_case: Load case name to filter
        case_field: Name of load case field
    
    Returns:
        Filtered list
    """
    return [item for item in data if item.get(case_field) == load_case]


# ==================== ENUMERATIONS HELPERS ====================

LOAD_PATTERN_TYPES = {
    'DEAD': 1,
    'SUPERDEAD': 2,
    'LIVE': 3,
    'LIVE_REDUCIBLE': 4,
    'QUAKE': 5,
    'WIND': 6,
    'SNOW': 7,
    'OTHER': 8,
    'MOVE': 9,
    'TEMPERATURE': 10,
    'ROOF_LIVE': 11,
    'NOTIONAL': 12,
    'PATTERN_LIVE': 13
}


def get_load_type_code(load_type_name: str) -> int:
    """
    Get numeric code for load pattern type.
    
    Args:
        load_type_name: Load type name (e.g., 'DEAD', 'LIVE')
    
    Returns:
        Numeric code
    """
    code = LOAD_PATTERN_TYPES.get(load_type_name.upper())
    if code is None:
        raise ValueError(
            f"Unknown load type: {load_type_name}. "
            f"Valid options: {list(LOAD_PATTERN_TYPES.keys())}"
        )
    return code


def get_load_type_name(code: int) -> str:
    """
    Get load pattern type name from code.
    
    Args:
        code: Numeric load type code
    
    Returns:
        Load type name
    """
    for name, type_code in LOAD_PATTERN_TYPES.items():
        if type_code == code:
            return name
    return f"UNKNOWN_{code}"