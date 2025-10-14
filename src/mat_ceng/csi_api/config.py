# src/csi_api/config.py

import os
import yaml
from pathlib import Path

def get_project_root_folder():
        here = Path(__file__).resolve()
        project_root = here.parent
        while project_root.name != "src":
            project_root = project_root.parent
        project_root = project_root.parent  # Now at project root
        return project_root

def load_config(config_path=None):
    """
    Load configuration from YAML file.
    If no path given, looks for 'config.yaml' in project root.
    """
    if config_path is None:
        # Assume config.yaml is in the same dir as pyproject.toml
        #config_path = Path(__file__).parent.parent.parent.parent / "config.yaml"
        project_root = get_project_root_folder()
        config_path = project_root / "config.yaml"
    else:
        config_path = Path(config_path)

    if not config_path.exists():
        raise FileNotFoundError(f"Config file not found: {config_path}")

    with open(config_path, 'r') as f:
        config = yaml.safe_load(f)

    # Ensure log directory exists
    log_dir = config.get("logging", {}).get("log_dir", "logs")
    Path(log_dir).mkdir(exist_ok=True)

    return config
