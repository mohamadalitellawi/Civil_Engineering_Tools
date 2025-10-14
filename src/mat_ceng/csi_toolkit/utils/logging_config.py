"""
Logging configuration for CSI Toolkit.

Uses loguru for enhanced logging with rotation and formatting.
"""

import sys
from pathlib import Path
from loguru import logger
from typing import Optional


def setup_logging(
    log_level: str = "INFO",
    log_file: Optional[str] = None,
    rotation: str = "10 MB",
    retention: str = "1 week",
    console_output: bool = True
) -> None:
    """
    Configure logging for the application.
    
    Args:
        log_level: Logging level (DEBUG, INFO, WARNING, ERROR, CRITICAL)
        log_file: Path to log file. If None, logs to 'logs/csi_toolkit.log'
        rotation: When to rotate log file (e.g., "10 MB", "1 day")
        retention: How long to keep old logs
        console_output: Whether to output logs to console
    
    Example:
        >>> setup_logging(log_level="DEBUG", log_file="my_project.log")
    """
    # Remove default handler
    logger.remove()
    
    # Console handler with color
    if console_output:
        logger.add(
            sys.stdout,
            format="<green>{time:YYYY-MM-DD HH:mm:ss}</green> | "
                   "<level>{level: <8}</level> | "
                   "<cyan>{name}</cyan>:<cyan>{function}</cyan>:<cyan>{line}</cyan> | "
                   "<level>{message}</level>",
            level=log_level,
            colorize=True
        )
    
    # File handler with rotation
    if log_file is None:
        log_dir = Path("logs")
        log_dir.mkdir(exist_ok=True)
        log_file = log_dir / "csi_toolkit.log"
    
    logger.add(
        log_file,
        format="{time:YYYY-MM-DD HH:mm:ss} | {level: <8} | {name}:{function}:{line} | {message}",
        level=log_level,
        rotation=rotation,
        retention=retention,
        compression="zip",
        enqueue=True  # Thread-safe
    )
    
    logger.info(f"Logging initialized - Level: {log_level}")


def get_logger(name: str):
    """
    Get a logger instance with the given name.
    
    Args:
        name: Logger name (typically __name__)
    
    Returns:
        Logger instance
    """
    return logger.bind(name=name)