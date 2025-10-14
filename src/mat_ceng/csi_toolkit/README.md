# CSI Toolkit

Professional Python library for working with CSI software APIs (ETABS, SAP2000, SAFE).

## Features

- 🏗️ **Modular Architecture**: Separate modules for each CSI software with shared utilities
- 📊 **Comprehensive Functionality**: Connect, create, manipulate, analyze, and extract results
- 🔧 **Production Ready**: Full logging, exception handling, and type hints
- 📈 **Results Export**: Export analysis results to Excel, CSV, or custom formats
- 🎯 **Easy to Use**: High-level API with sensible defaults
- ⚡ **Modern Python**: Built with Python 3.13 and UV package manager

## Supported Software

- ETABS v22 (fully implemented)
- SAP2000 (structure ready, examples TBD)
- SAFE (structure ready, examples TBD)

## Installation

### Prerequisites

1. **Python 3.13**: Download from [python.org](https://www.python.org/)
2. **UV Package Manager**: Install with:
   ```bash
   pip install uv
   ```
3. **CSI Software**: ETABS v22, SAP2000, or SAFE must be installed

### Install the Package

```bash
# Clone the repository
git clone <your-repo-url>
cd csi-api-toolkit

# Install dependencies with UV
uv sync

# Or install in development mode
uv pip install -e .
```

## Quick Start

### Basic ETABS Connection

```python
from csi_toolkit import ETABSAPI, setup_logging

# Setup logging
setup_logging(log_level="INFO")

# Connect to ETABS
with ETABSAPI() as etabs:
    # Create new instance
    etabs.connect(visible=True)
    
    # Create a simple model
    etabs.create_template_model(
        num_stories=5,
        story_height=3.5,
        num_bays_x=3,
        bay_width_x=6.0
    )
    
    # Save model
    etabs.save_model("my_building.edb")
```

### Complete Workflow Example

See `examples/etabs_complete_example.py` for a comprehensive workflow that includes:
- Model creation from template
- Material and section definition
- Element manipulation
- Load application
- Analysis execution
- Results extraction
- Excel export

Run it with:
```bash
uv run examples/etabs_complete_example.py
```

## Project Structure

```
csi-api-toolkit/
├── src/csi_toolkit/
│   ├── core/                 # Shared functionality
│   │   ├── base_api.py      # Base API class
│   │   ├── connection.py    # Connection manager
│   │   └── exceptions.py    # Custom exceptions
│   ├── etabs/               # ETABS-specific modules
│   │   ├── api.py          # Main ETABS API
│   │   ├── elements.py     # Element manipulation
│   │   ├── loads.py        # Load definitions
│   │   └── results.py      # Results extraction
│   ├── sap2000/            # SAP2000 modules (TBD)
│   ├── safe/               # SAFE modules (TBD)
│   └── utils/              # Utility functions
│       ├── logging_config.py
│       ├── helpers.py
│       └── validators.py
├── examples/               # Usage examples
├── tests/                 # Unit tests
└── docs/                  # Documentation
```

## Usage Guide

### 1. Connection Management

```python
from csi_toolkit.etabs import ETABSAPI

# Create new instance
etabs = ETABSAPI()
etabs.connect(attach_to_existing=False, visible=True)

# Or attach to existing instance
etabs.connect(attach_to_existing=True)

# Or open existing model
etabs.connect(model_path="existing_model.edb")
```

### 2. Element Manipulation

```python
from csi_toolkit.etabs.elements import ETABSElements

elements = ETABSElements(etabs.model)

# Add material
elements.add_material(name="C30", material_type=2)

# Add frame section
elements.add_frame_section_rectangular(
    name="COL400x400",
    material="C30",
    depth=0.4,
    width=0.4
)

# Add point
point = elements.add_point(x=0, y=0, z=0)

# Add frame
frame = elements.add_frame(point1="1", point2="2", section="COL400x400")

# Get all frames as DataFrame
frames_df = elements.get_all_frames()
```

### 3. Load Definition

```python
from csi_toolkit.etabs.loads import ETABSLoads
from csi_toolkit.utils.helpers import get_load_type_code

loads = ETABSLoads(etabs.model)

# Add load pattern
loads.add_load_pattern(
    name="LIVE",
    load_type=get_load_type_code("LIVE"),
    self_weight_multiplier=0.0
)

# Apply uniform load to area
loads.add_area_uniform_load(
    area_name="Floor1",
    load_pattern="LIVE",
    value=3.0  # kN/m²
)

# Apply distributed load to frame
loads.add_frame_distributed_load(
    frame_name="Beam1",
    load_pattern="LIVE",
    load_type=1,
    direction=6,
    distance1=0.0,
    distance2=1.0,
    value1=-10.0,
    value2=-10.0
)

# Create load combination
loads.add_load_combination(name="COMB1", combo_type=0)
loads.set_combination_case("COMB1", "DEAD", 1.2)
loads.set_combination_case("COMB1", "LIVE", 1.6)
```

### 4. Analysis and Results

```python
from csi_toolkit.etabs.results import ETABSResults

# Run analysis
etabs.run_analysis()

# Extract results
results = ETABSResults(etabs.model)

# Get joint reactions
reactions_df = results.get_joint_reactions(load_case="DEAD")

# Get joint displacements
displ_df = results.get_joint_displacements(load_case="COMB1")

# Get frame forces
forces_df = results.get_frame_forces(load_case="COMB1")

# Get modal periods
periods_df = results.get_modal_periods()

# Export all results to Excel
results.export_results_to_excel("results.xlsx", load_case="COMB1")
```

### 5. Utilities

```python
from csi_toolkit.utils.helpers import (
    get_unit_codes,
    get_load_type_code,
    grid_points_rectangular
)

# Get unit codes for API
force_code, length_code = get_unit_codes('kN', 'm')
etabs.set_model_units(force_code, length_code)

# Generate grid points
points = grid_points_rectangular(
    x_start=0, x_end=18, x_spacing=6,
    y_start=0, y_end=18, y_spacing=6,
    z=0
)
```

## Logging

The toolkit uses `loguru` for comprehensive logging:

```python
from csi_toolkit.utils.logging_config import setup_logging

# Configure logging
setup_logging(
    log_level="DEBUG",
    log_file="my_project.log",
    rotation="10 MB",
    retention="1 week",
    console_output=True
)
```

Logs include:
- Connection events
- API calls and responses
- Errors with full stack traces
- Performance metrics
- File operations

## Exception Handling

All operations use custom exceptions for clear error messages:

```python
from csi_toolkit.exceptions import (
    ConnectionError,
    ModelError,
    ElementError,
    LoadError,
    ResultsError
)

try:
    etabs.connect()
except ConnectionError as e:
    print(f"Failed to connect: {e}")
```

## Development

### Running Tests

```bash
# Run all tests
uv run pytest

# Run with coverage
uv run pytest --cov=csi_toolkit --cov-report=html

# Run specific test file
uv run pytest tests/test_etabs.py
```

### Code Formatting

```bash
# Format code with black
uv run black src/

# Lint with ruff
uv run ruff check src/

# Type checking with mypy
uv run mypy src/
```

### Adding New Features

1. Add functionality to appropriate module
2. Include comprehensive docstrings
3. Add logging statements
4. Handle exceptions appropriately
5. Add tests
6. Update examples

## Best Practices

1. **Always use context managers** for automatic cleanup:
   ```python
   with ETABSAPI() as etabs:
       # Your code here
       pass
   # Automatically disconnects
   ```

2. **Check analysis results** before extracting:
   ```python
   etabs.run_analysis()
   # Give ETABS time to complete
   results = ETABSResults(etabs.model)
   ```

3. **Save your work frequently**:
   ```python
   etabs.save_model("backup.edb")
   ```

4. **Use logging** for debugging:
   ```python
   setup_logging(log_level="DEBUG")
   ```

## Common Issues

### Issue: "Software not found"
**Solution**: Provide custom installation path:
```python
etabs = ETABSAPI(installation_path=r"C:\Your\Path\ETABS 22")
```

### Issue: "Failed to load API DLL"
**Solution**: Ensure pythonnet is installed and CSI software is properly installed.

### Issue: "No analysis results available"
**Solution**: Run analysis first with `etabs.run_analysis()`

## Contributing

Contributions are welcome! Please:
1. Fork the repository
2. Create a feature branch
3. Add tests for new functionality
4. Ensure all tests pass
5. Submit a pull request

## License

MIT License - See LICENSE file for details

## Support

For issues and questions:
- GitHub Issues: <your-repo-url>/issues
- Email: your.email@example.com

## Acknowledgments

- Built with pythonnet for .NET interop
- Uses loguru for logging
- Inspired by the CSI API documentation

## Roadmap

- [ ] Complete SAP2000 implementation
- [ ] Complete SAFE implementation
- [ ] Add more examples
- [ ] Implement design code checks
- [ ] Add visualization capabilities
- [ ] Create GUI wrapper
- [ ] Add batch processing utilities