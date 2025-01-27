import logging
import sys
from typing import Optional


class LogFormatter(logging.Formatter):
    """Custom formatter adding colors to log levels in console output"""

    COLORS = {
        "DEBUG": "\033[0;36m",  # Cyan
        "INFO": "\033[0;32m",  # Green
        "WARNING": "\033[0;33m",  # Yellow
        "ERROR": "\033[0;31m",  # Red
        "CRITICAL": "\033[0;35m",  # Magenta
        "RESET": "\033[0m",  # Reset
    }

    def format(self, record):
        # Add colors if it's going to stdout/stderr
        if record.levelname in self.COLORS:
            record.levelname = f"{self.COLORS[record.levelname]}{record.levelname}{self.COLORS['RESET']}"
        return super().format(record)


def setup_logging(
    log_level: str = "INFO",
    logger_name: Optional[str] = None,
    format_string: str = "%(asctime)s - %(name)s - %(levelname)s - %(message)s",
) -> logging.Logger:
    """
    Sets up logging configuration with colored console output.

    Args:
        log_level: Logging level (DEBUG, INFO, WARNING, ERROR, CRITICAL)
        logger_name: Optional name for the logger. If None, returns root logger
        format_string: Optional custom format string for log messages

    Returns:
        Configured logger instance
    """

    # Get the appropriate logger
    logger = logging.getLogger(logger_name) if logger_name else logging.getLogger()

    # Clear any existing handlers
    logger.handlers.clear()

    # Set the log level
    try:
        logger.setLevel(getattr(logging, log_level.upper()))
    except AttributeError:
        logger.setLevel(logging.INFO)
        logger.warning(f"Invalid log level '{log_level}', defaulting to INFO")

    # Create console handler with custom formatter
    console_handler = logging.StreamHandler(sys.stdout)
    console_handler.setFormatter(LogFormatter(format_string))
    logger.addHandler(console_handler)

    # Set lower log levels for noisy third-party libraries
    for lib in ["aiobotocore", "botocore", "urllib3"]:
        logging.getLogger(lib).setLevel(logging.WARNING)

    return logger
