# src/csi_api/core/utils.py

import sys
from pathlib import Path
from loguru import logger
from ..config import load_config

def setup_logger(config=None):
    """Configure loguru logger using config."""
    if config is None:
        config = load_config()

    log_config = config.get("logging", {})
    level = log_config.get("level", "INFO")
    log_to_file = log_config.get("log_to_file", True)
    log_dir = log_config.get("log_dir", "logs")

    logger.remove()
    log_format = "<green>{time:YYYY-MM-DD HH:mm:ss}</green> | <level>{level: <8}</level> | <cyan>{name}</cyan>:<cyan>{function}</cyan>:<cyan>{line}</cyan> - <level>{message}</level>"
    logger.add(sys.stderr, format=log_format, level=level)

    if log_to_file:
        log_path = Path(log_dir) / "csi_api.log"
        logger.add(
            log_path,
            rotation="10 MB",
            retention="1 week",
            format=log_format,
            level=level
        )
    return logger

def validate_software_path(path):
    """Validate that software executable exists."""
    exe_path = Path(path)
    if not exe_path.exists():
        raise FileNotFoundError(f"CSI software not found at: {exe_path}")
    return str(exe_path)
