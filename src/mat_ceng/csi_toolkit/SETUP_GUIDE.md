# Complete Setup Guide for CSI Toolkit

This guide will walk you through setting up the CSI Toolkit from scratch.

## Table of Contents
1. [Prerequisites](#prerequisites)
2. [System Setup](#system-setup)
3. [Project Creation](#project-creation)
4. [Dependency Installation](#dependency-installation)
5. [VS Code Configuration](#vs-code-configuration)
6. [Verification](#verification)
7. [First Run](#first-run)
8. [Troubleshooting](#troubleshooting)

---

## Prerequisites

### Required Software

1. **Python 3.13**
   - Download from: https://www.python.org/downloads/
   - During installation, check "Add Python to PATH"
   - Verify: Open Command Prompt and run `python --version`

2. **VS Code**
   - Download from: https://code.visualstudio.com/
   - Install Python extension from Extensions marketplace

3. **UV Package Manager**
   - Install after Python is ready
   - Method 1 (PowerShell):
     ```powershell
     powershell -c "irm https://astral.sh/uv/install.ps1 | iex"
     ```
   - Method 2 (pip):
     ```bash
     pip install uv
     ```
   - Verify: `uv --version`

4. **ETABS v22** (or SAP2000/SAFE)
   - Must be installed with API components
   - Default path: `C:\Program Files\Computers and Structures\ETABS 22`
   - Verify installation includes API DLL files

### Optional but Recommended

- **Git**: For version control
- **Windows Terminal**: Better command-line experience

---

## System Setup

### Step 1: Create Project Directory

```bash
# Open Command Prompt or PowerShell
# Navigate to where you want the project
cd C:\Users\YourName\Documents\Engineering

# Create project directory
mkdir csi-api-toolkit
cd csi-api-toolkit
```

### Step 2: Initialize UV Project

```bash
# Initialize new Python project with UV
uv init --python 3.13

# This creates:
# - pyproject.toml
# - .python-version
# - Basic project structure
```

---

## Project Creation

### Step 3: Create Directory Structure

Run these commands in PowerShell:

```powershell
# Create source directory structure
New-Item -ItemType Directory -Path "src/csi_toolkit/core" -Force
New-Item -ItemType Directory -Path "src/csi_toolkit/etabs" -Force
New-Item -ItemType Directory -Path "src/csi_toolkit/sap2000" -Force
New-Item -ItemType Directory -Path "src/csi_toolkit/safe" -Force
New-Item -ItemType Directory -Path "src/csi_toolkit/utils" -Force

# Create test directories
New-Item -ItemType Directory -Path "tests" -Force

# Create examples directory
New-Item -ItemType Directory -Path "examples" -Force

# Create docs and logs directories
New-Item -ItemType Directory -Path "docs" -Force
New-Item -ItemType Directory -Path "logs" -Force

# Create output directory for results
New-Item -ItemType Directory -Path "output" -Force
```

Or in Command Prompt:

```cmd
mkdir src\csi_toolkit\core
mkdir src\csi_toolkit\etabs
mkdir src\csi_toolkit\sap2000
mkdir src\csi_toolkit\safe
mkdir src\csi_toolkit\utils
mkdir tests
mkdir examples
mkdir docs
mkdir logs
mkdir output
```

### Step 4: Create __init__.py Files

```bash
# Create empty __init__.py files
type nul > src/csi_toolkit/__init__.py
type nul > src/csi_toolkit/core/__init__.py
type nul > src/csi_toolkit/etabs/__init__.py
type nul > src/csi_toolkit/sap2000/__init__.py
type nul > src/csi_toolkit/safe/__init__.py
type nul > src/csi_toolkit/utils/__init__.py
type nul > tests/__init__.py
```

### Step 5: Copy Code Files

Now copy all the code files I provided into their respective locations:

**Core modules** (in `src/csi_toolkit/core/`):
- `exceptions.py`
- `connection.py`
- `base_api.py`

**Utils modules** (in `src/csi_toolkit/utils/`):
- `logging_config.py`
- `helpers.py`
- `validators.py` (create empty for now)

**ETABS modules** (in `src/csi_toolkit/etabs/`):
- `api.py`
- `elements.py`
- `loads.py`
- `results.py`

**Examples** (in `examples/`):
- `etabs_complete_example.py`

**Root files**:
- `README.md`
- `SETUP_GUIDE.md` (this file)

---

## Dependency Installation

### Step 6: Configure pyproject.toml

Copy this content to `pyproject.toml`:

```toml
[project]
name = "csi-toolkit"
version = "0.1.0"
description = "Professional Python toolkit for CSI software API integration"
requires-python = ">=3.13"
dependencies = [
    "pythonnet>=3.0.3",
    "pandas>=2.2.0",
    "numpy>=1.26.0",
    "loguru>=0.7.2",
    "pydantic>=2.5.0",
    "typing-extensions>=4.9.0",
    "openpyxl>=3.1.0",
]

[project.optional-dependencies]
dev = [
    "pytest>=7.4.0",
    "pytest-cov>=4.1.0",
    "black>=23.12.0",
    "ruff>=0.1.9",
    "mypy>=1.8.0",
]

[build-system]
requires = ["hatchling"]
build-backend = "hatchling.build"

[tool.hatch.build.targets.wheel]
packages = ["src/csi_toolkit"]
```

### Step 7: Install Dependencies

```bash
# Sync all dependencies (creates virtual environment)
uv sync

# This will:
# 1. Create .venv directory
# 2. Install all dependencies
# 3. Set up the project in development mode

# Install dev dependencies too
uv sync --all-extras
```

### Step 8: Verify Installation

```bash
# Activate virtual environment
# Windows Command Prompt:
.venv\Scripts\activate

# Windows PowerShell:
.venv\Scripts\Activate.ps1

# Verify Python
python --version  # Should show 3.13.x

# Check installed packages
uv pip list

# Should see: pythonnet, pandas, numpy, loguru, etc.
```

---

## VS Code Configuration

### Step 9: Open Project in VS Code

```bash
# From project directory
code .
```

### Step 10: Configure Python Interpreter

1. Press `Ctrl+Shift+P`
2. Type "Python: Select Interpreter"
3. Choose the interpreter from `.venv` directory
   - Should show: `Python 3.13.x ('.venv': venv)`

### Step 11: Create VS Code Settings

Create `.vscode/settings.json`:

```json
{
    "python.defaultInterpreterPath": "${workspaceFolder}/.venv/Scripts/python.exe",
    "python.terminal.activateEnvironment": true,
    "python.testing.pytestEnabled": true,
    "python.testing.unittestEnabled": false,
    "python.linting.enabled": true,
    "python.linting.pylintEnabled": false,
    "python.linting.ruffEnabled": true,
    "python.formatting.provider": "black",
    "editor.formatOnSave": true,
    "editor.rulers": [100],
    "files.exclude": {
        "**/__pycache__": true,
        "**/.pytest_cache": true,
        "**/*.pyc": true
    },
    "python.analysis.extraPaths": [
        "${workspaceFolder}/src"
    ]
}
```

### Step 12: Create Launch Configuration

Create `.vscode/launch.json`:

```json
{
    "version": "0.2.0",