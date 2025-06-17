"""
Logging utility for the PowerFactory network analysis application.
"""

import logging
import logging.handlers
from pathlib import Path
from typing import Optional
from datetime import datetime


def setup_logger(
    name: Optional[str] = None,
    level: str = "INFO",
    log_file: Optional[Path] = None,
    console_logging: bool = True,
    file_logging: bool = True,
    max_file_size_mb: int = 50,
    backup_count: int = 5
) -> logging.Logger:
    """
    Set up a logger with both file and console handlers.
    
    Args:
        name: Logger name (defaults to root logger)
        level: Logging level
        log_file: Path to log file (auto-generated if None)
        console_logging: Enable console output
        file_logging: Enable file output
        max_file_size_mb: Maximum log file size in MB
        backup_count: Number of backup files to keep
        
    Returns:
        Configured logger instance
    """
    logger = logging.getLogger(name)
    
    # Avoid duplicate handlers
    if logger.handlers:
        return logger
    
    # Set logging level
    log_level = getattr(logging, level.upper(), logging.INFO)
    logger.setLevel(log_level)
    
    # Create formatter
    formatter = logging.Formatter(
        '%(asctime)s - %(name)s - %(levelname)s - %(message)s',
        datefmt='%Y-%m-%d %H:%M:%S'
    )
    
    # Console handler
    if console_logging:
        console_handler = logging.StreamHandler()
        console_handler.setLevel(log_level)
        console_handler.setFormatter(formatter)
        logger.addHandler(console_handler)
    
    # File handler
    if file_logging:
        if log_file is None:
            # Auto-generate log file path
            timestamp = datetime.now().strftime('%Y%m%d')
            log_dir = Path(__file__).parent.parent.parent / "output" / "logs"
            log_dir.mkdir(parents=True, exist_ok=True)
            log_file = log_dir / f"network_analysis_{timestamp}.log"
        
        # Rotating file handler
        file_handler = logging.handlers.RotatingFileHandler(
            log_file,
            maxBytes=max_file_size_mb * 1024 * 1024,
            backupCount=backup_count
        )
        file_handler.setLevel(log_level)
        file_handler.setFormatter(formatter)
        logger.addHandler(file_handler)
    
    return logger


def get_logger(name: str) -> logging.Logger:
    """
    Get a logger instance with consistent configuration.
    
    Args:
        name: Logger name
        
    Returns:
        Logger instance
    """
    return logging.getLogger(name)


class AnalysisLogger:
    """
    Specialized logger for analysis operations with progress tracking.
    """
    
    def __init__(self, name: str):
        """Initialize analysis logger."""
        self.logger = get_logger(name)
        self._start_time: Optional[datetime] = None
        self._operation_count = 0
    
    def start_operation(self, operation_name: str, total_items: int = 0) -> None:
        """
        Start a new operation with progress tracking.
        
        Args:
            operation_name: Name of the operation
            total_items: Total number of items to process
        """
        self._start_time = datetime.now()
        self._operation_count = 0
        self.logger.info(f"Starting {operation_name}")
        if total_items > 0:
            self.logger.info(f"Processing {total_items} items")
    
    def log_progress(self, current: int, total: int, message: str = "") -> None:
        """
        Log progress of current operation.
        
        Args:
            current: Current item number
            total: Total number of items
            message: Optional additional message
        """
        if total > 0:
            percentage = (current / total) * 100
            if current % max(1, total // 10) == 0:  # Log every 10%
                elapsed = self._get_elapsed_time()
                self.logger.info(f"Progress: {current}/{total} ({percentage:.1f}%) {message} - Elapsed: {elapsed}")
    
    def complete_operation(self, operation_name: str, success: bool = True) -> None:
        """
        Complete the current operation.
        
        Args:
            operation_name: Name of the operation
            success: Whether operation completed successfully
        """
        elapsed = self._get_elapsed_time()
        status = "completed successfully" if success else "failed"
        self.logger.info(f"{operation_name} {status} in {elapsed}")
    
    def _get_elapsed_time(self) -> str:
        """Get elapsed time since operation start."""
        if self._start_time:
            elapsed = datetime.now() - self._start_time
            minutes, seconds = divmod(elapsed.total_seconds(), 60)
            return f"{int(minutes):02d}:{int(seconds):02d}"
        return "00:00"
    
    def error(self, message: str, exc_info: bool = False) -> None:
        """Log error message."""
        self.logger.error(message, exc_info=exc_info)
    
    def warning(self, message: str) -> None:
        """Log warning message."""
        self.logger.warning(message)
    
    def info(self, message: str) -> None:
        """Log info message."""
        self.logger.info(message)
    
    def debug(self, message: str) -> None:
        """Log debug message."""
        self.logger.debug(message)
