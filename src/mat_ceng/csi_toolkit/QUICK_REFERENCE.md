# CSI Toolkit - Quick Reference Card

## Import Statements

```python
# Main API
from csi_toolkit.etabs import ETABSAPI
from csi_toolkit.etabs.elements import ETABSElements
from csi_toolkit.etabs.loads import ETABSLoads
from csi_toolkit.etabs.results import ETABSResults

# Utilities
from csi_toolkit.utils.logging_config import setup_logging
from csi_toolkit.utils.helpers import get_unit_codes, get_load_type_code

# Exceptions
from csi_toolkit.core.exceptions import (
    ConnectionError, ModelError, ElementError, LoadError, ResultsError
)
```

## Basic Workflow

```python
# 1. Setup
setup_logging(log_level="INFO")

# 2. Connect
with ETABSAPI() as etabs:
    etabs.connect(visible=True)
    
    # 3. Create/Open Model
    etabs.create_template_model(num_stories=5, story_height=3.5)
    
    # 4. Work with model
    etabs.unlock_model()
    elements = ETABSElements(etabs.model)
    loads = ETABSLoads(etabs.model)
    
    # 5. Save & Analyze
    etabs.save_model("model.edb")
    etabs.run_analysis()
    
    # 6. Get Results
    results = ETABSResults(etabs.model)
    df = results.get_joint_reactions()
```

## Connection Methods

```python
# New instance
etabs.connect(attach_to_existing=False, visible=True)

# Attach to existing
etabs.connect(attach_to_existing=True)

# Open existing model
etabs.connect(model_path="existing.edb", visible=True)
```

## Model Operations

```python
# Units
force_code, length_code = get_unit_codes('kN', 'm')
etabs.set_model_units(force_code, length_code)

# Model state
etabs.unlock_model()
etabs.lock_model()
etabs.refresh_view()

# Save
etabs.save_model("path/to/model.edb")

# Analysis
etabs.run_analysis()

# Info
counts = etabs.get_element_count()  # {'points': 24, 'frames': 48, ...}
info = etabs.get_project_info()
etabs.set_project_info("Engineer", "John Doe")
```

## Materials & Sections

```python
elements = ETABSElements(etabs.model)

# Material
elements.add_material(name="C30", material_type=2)  # 2=Concrete, 1=Steel

# Frame section
elements.add_frame_section_rectangular(
    name="COL400", material="C30", depth=0.4, width=0.4
)

# Slab section
elements.add_slab_section(
    name="SLAB200", slab_type=1, material="C30", thickness=0.2
)
```

## Elements

```python
# Point
point = elements.add_point(x=0, y=0, z=0, name="P1")

# Frame
frame = elements.add_frame(point1="P1", point2="P2", section="COL400")

# Area
area = elements.add_area_by_points(points=["P1", "P2", "P3", "P4"])

# Get elements
frames_df = elements.get_all_frames()
points_df = elements.get_all_points()
areas_df = elements.get_all_areas()

# Modify
elements.set_frame_section(frame_name="F1", section_name="BEAM300")
```

## Load Patterns

```python
loads = ETABSLoads(etabs.model)

# Create pattern
loads.add_load_pattern(
    name="DEAD",
    load_type=get_load_type_code("DEAD"),  # or 1
    self_weight_multiplier=1.0
)

# Load types: DEAD=1, SUPERDEAD=2, LIVE=3, QUAKE=5, WIND=6
```

## Point Loads

```python
loads.add_point_load(
    point_name="P1",
    load_pattern="LIVE",
    force_x=0, force_y=0, force_z=-100,  # kN
    moment_x=0, moment_y=0, moment_z=0
)
```

## Frame Loads

```python
# Distributed load
loads.add_frame_distributed_load(
    frame_name="F1",
    load_pattern="LIVE",
    load_type=1,        # 1=Force, 2=Moment
    direction=6,        # 6=Gravity
    distance1=0.0,
    distance2=1.0,
    value1=-10.0,       # kN/m
    value2=-10.0,
    relative_distance=True
)

# Point load
loads.add_frame_point_load(
    frame_name="F1",
    load_pattern="LIVE",
    load_type=1,
    direction=6,
    distance=0.5,       # midspan
    value=-50.0,        # kN
    relative_distance=True
)
```

## Area Loads

```python
loads.add_area_uniform_load(
    area_name="A1",
    load_pattern="LIVE",
    value=3.0,          # kN/m²
    direction=6         # Gravity
)
```

## Load Combinations

```python
# Create combo
loads.add_load_combination(name="COMB1", combo_type=0)  # 0=Linear

# Add cases
loads.set_combination_case("COMB1", "DEAD", 1.2)
loads.set_combination_case("COMB1", "LIVE", 1.6)
```

## Results Extraction

```python
results = ETABSResults(etabs.model)

# Joint results
reactions = results.get_joint_reactions(load_case="DEAD")
displ = results.get_joint_displacements(load_case="COMB1")

# Frame results
forces = results.get_frame_forces(load_case="COMB1")
forces = results.get_frame_forces(load_case="COMB1", frame_name="F1")

# Area results
area_forces = results.get_area_forces(load_case="COMB1")
stresses = results.get_area_stresses(load_case="COMB1")

# Story results
story_forces = results.get_story_forces(load_case="WIND")

# Modal results
periods = results.get_modal_periods()
participation = results.get_modal_participation_factors()

# Export
results.export_results_to_excel("results.xlsx", load_case="COMB1")
```

## Result DataFrames

```python
# Joint Reactions columns:
# Joint, LoadCase, StepType, StepNum, F1, F2, F3, M1, M2, M3

# Joint Displacements columns:
# Joint, LoadCase, StepType, StepNum, U1, U2, U3, R1, R2, R3

# Frame Forces columns:
# Frame, LoadCase, Distance, P, V2, V3, T, M2, M3

# Area Forces columns:
# Area, LoadCase, F11, F22, F12, M11, M22, M12, V13, V23

# Find max values
max_reaction = reactions['F3'].abs().max()
max_displ = displ['U3'].abs().max()
max_moment = forces['M3'].abs().max()
```

## Helper Functions

```python
from csi_toolkit.utils.helpers import *

# Units
force_code, length_code = get_unit_codes('kN', 'm')
# Options: 'lb', 'kip', 'N', 'kN', 'kgf', 'tonf'
# Options: 'in', 'ft', 'mm', 'cm', 'm'

# Load types
load_type = get_load_type_code('LIVE')
# Options: DEAD, SUPERDEAD, LIVE, QUAKE, WIND, SNOW, etc.

# File operations
path = ensure_file_extension("model", ".edb")
validate_file_exists("existing_model.edb")
create_directory("output/results")

# Grid generation
points = grid_points_rectangular(
    x_start=0, x_end=18, x_spacing=6,
    y_start=0, y_end=18, y_spacing=6,
    z=0
)

# Distance
dist = calculate_distance_3d(x1, y1, z1, x2, y2, z2)
```

## Logging

```python
from csi_toolkit.utils.logging_config import setup_logging

setup_logging(
    log_level="DEBUG",              # DEBUG, INFO, WARNING, ERROR
    log_file="my_project.log",
    rotation="10 MB",
    retention="1 week",
    console_output=True
)

# Log levels in your code
from loguru import logger
logger.debug("Detailed info")
logger.info("General info")
logger.warning("Warning")
logger.error("Error occurred")
```

## Exception Handling

```python
from csi_toolkit.core.exceptions import *

try:
    etabs.connect()
except ConnectionError:
    print("Failed to connect to ETABS")
except SoftwareNotFoundError:
    print("ETABS not installed")
except ModelError:
    print("Model operation failed")
except ElementError:
    print("Element operation failed")
except LoadError:
    print("Load operation failed")
except ResultsError:
    print("Results extraction failed")
```

## Common Patterns

### Pattern 1: Batch Process Multiple Models

```python
from pathlib import Path

models = Path("models").glob("*.edb")

for model_path in models:
    with ETABSAPI() as etabs:
        etabs.connect(model_path=str(model_path), visible=False)
        etabs.run_analysis()
        
        results = ETABSResults(etabs.model)
        results.export_results_to_excel(f"results/{model_path.stem}.xlsx")
```

### Pattern 2: Extract Maximum Values

```python
results = ETABSResults(etabs.model)
forces = results.get_frame_forces(load_case="COMB1")

# Find maximum moment and which frame
max_idx = forces['M3'].abs().idxmax()
max_frame = forces.loc[max_idx]
print(f"Max moment: {max_frame['M3']} in frame {max_frame['Frame']}")
```

### Pattern 3: Apply Loads to Multiple Elements

```python
loads = ETABSLoads(etabs.model)
elements = ETABSElements(etabs.model)

areas = elements.get_all_areas()
for _, area in areas.iterrows():
    loads.add_area_uniform_load(
        area_name=area['Name'],
        load_pattern="LIVE",
        value=3.0
    )
```

### Pattern 4: Parametric Model Creation

```python
def create_building(stories, bay_width):
    with ETABSAPI() as etabs:
        etabs.connect(visible=False)
        etabs.create_template_model(
            num_stories=stories,
            story_height=3.5,
            num_bays_x=3,
            bay_width_x=bay_width
        )
        etabs.save_model(f"building_{stories}st_{bay_width}m.edb")

for stories in [3, 5, 7]:
    for width in [5, 6, 7]:
        create_building(stories, width)
```

## Unit Codes Reference

| Force    | Code | Length  | Code |
|----------|------|---------|------|
| lb       | 1    | in      | 1    |
| kip      | 2    | ft      | 2    |
| N        | 3    | micron  | 3    |
| kN       | 4    | mm      | 4    |
| kgf      | 5    | cm      | 5    |
| tonf     | 6    | m       | 6    |

## Load Direction Codes

| Direction        | Code |
|------------------|------|
| Local 1          | 1    |
| Local 2          | 2    |
| Local 3          | 3    |
| Global X         | 4    |
| Global Y         | 5    |
| Global Z (Grav)  | 6    |

## Tips & Best Practices

1. **Always use context managers** (`with` statement) for automatic cleanup
2. **Unlock model** before editing: `etabs.unlock_model()`
3. **Save frequently**: `etabs.save_model("backup.edb")`
4. **Check results exist** before extraction
5. **Use relative distances** for frame loads (0 to 1)
6. **Set units explicitly** at start of script
7. **Enable logging** for debugging
8. **Handle exceptions** appropriately
9. **Close ETABS** manually or call `disconnect()` when done

## Keyboard Shortcuts (VS Code)

- `F5` - Run with debugger
- `Ctrl+F5` - Run without debugger
- `Ctrl+Shift+P` - Command palette
- `Ctrl+`` - Toggle terminal
- `Ctrl+/` - Comment/uncomment

## Useful Commands

```bash
# Run script
python script.py

# Run with UV
uv run script.py

# Format code
black script.py

# Check style
ruff check script.py

# Run tests
pytest

# Install new package
uv add package-name
```

---

**Remember:** This is a reference card. See full documentation in README.md and examples/ directory.