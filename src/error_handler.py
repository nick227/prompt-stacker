"""
Error Handling and Logging System

Centralized error handling and logging for the Cursor automation system.
Provides consistent error handling, logging, and user feedback.
"""

import logging
import sys
from datetime import datetime
from enum import Enum
from tkinter import messagebox
from typing import Any, Callable, Dict, Optional

# =============================================================================
# ERROR TYPES
# =============================================================================


class ErrorSeverity(Enum):
    """Error severity levels."""

    INFO = "INFO"
    WARNING = "WARNING"
    ERROR = "ERROR"
    CRITICAL = "CRITICAL"


class ErrorCategory(Enum):
    """Error categories for classification."""

    UI = "UI"
    AUTOMATION = "AUTOMATION"
    FILE = "FILE"
    NETWORK = "NETWORK"
    SYSTEM = "SYSTEM"
    VALIDATION = "VALIDATION"
    UNKNOWN = "UNKNOWN"


# =============================================================================
# CUSTOM EXCEPTIONS
# =============================================================================


class AutomationError(Exception):
    """Base exception for automation-related errors."""

    def __init__(
        self,
        message: str,
        category: ErrorCategory = ErrorCategory.AUTOMATION,
        severity: ErrorSeverity = ErrorSeverity.ERROR,
        details: Optional[Dict[str, Any]] = None,
    ):
        super().__init__(message)
        self.message = message
        self.category = category
        self.severity = severity
        self.details = details or {}
        self.timestamp = datetime.now()


class UIError(AutomationError):
    """UI-related errors."""

    def __init__(
        self,
        message: str,
        severity: ErrorSeverity = ErrorSeverity.ERROR,
        details: Optional[Dict[str, Any]] = None,
    ):
        super().__init__(message, ErrorCategory.UI, severity, details)


class FileError(AutomationError):
    """File operation errors."""

    def __init__(
        self,
        message: str,
        severity: ErrorSeverity = ErrorSeverity.ERROR,
        details: Optional[Dict[str, Any]] = None,
    ):
        super().__init__(message, ErrorCategory.FILE, severity, details)


class ValidationError(AutomationError):
    """Validation errors."""

    def __init__(
        self,
        message: str,
        severity: ErrorSeverity = ErrorSeverity.WARNING,
        details: Optional[Dict[str, Any]] = None,
    ):
        super().__init__(message, ErrorCategory.VALIDATION, severity, details)


# =============================================================================
# LOGGING CONFIGURATION
# =============================================================================


class AutomationLogger:
    """Centralized logging for the automation system."""

    def __init__(self, log_file: str = None, level: int = logging.INFO):
        """Initialize the logger."""
        self.logger = logging.getLogger("prompt_stacker")
        self.logger.setLevel(level)

        # Use user-accessible log directory if no specific file provided
        if log_file is None:
            from pathlib import Path

            log_dir = Path.home() / "prompt_stacker_logs"
            log_dir.mkdir(exist_ok=True)
            log_file = str(log_dir / "automation.log")

        # Prevent duplicate handlers
        if not self.logger.handlers:
            self._setup_handlers(log_file)

    def _setup_handlers(self, log_file: str) -> None:
        """Setup logging handlers."""
        # File handler
        file_handler = logging.FileHandler(log_file, encoding="utf-8")
        file_handler.setLevel(logging.DEBUG)

        # Console handler
        console_handler = logging.StreamHandler(sys.stdout)
        console_handler.setLevel(logging.INFO)

        # Formatter
        formatter = logging.Formatter(
            "%(asctime)s - %(name)s - %(levelname)s - %(message)s",
            datefmt="%Y-%m-%d %H:%M:%S",
        )

        file_handler.setFormatter(formatter)
        console_handler.setFormatter(formatter)

        self.logger.addHandler(file_handler)
        self.logger.addHandler(console_handler)

    def info(self, message: str, **kwargs) -> None:
        """Log info message."""
        self.logger.info(message, extra=kwargs)

    def warning(self, message: str, **kwargs) -> None:
        """Log warning message."""
        self.logger.warning(message, extra=kwargs)

    def error(self, message: str, **kwargs) -> None:
        """Log error message."""
        self.logger.error(message, extra=kwargs)

    def critical(self, message: str, **kwargs) -> None:
        """Log critical message."""
        self.logger.critical(message, extra=kwargs)

    def debug(self, message: str, **kwargs) -> None:
        """Log debug message."""
        self.logger.debug(message, extra=kwargs)

    def exception(self, message: str, exc_info: bool = True, **kwargs) -> None:
        """Log exception with traceback."""
        self.logger.exception(message, extra=kwargs)


# =============================================================================
# ERROR HANDLER
# =============================================================================


class ErrorHandler:
    """Centralized error handling system."""

    def __init__(
        self,
        logger: Optional[AutomationLogger] = None,
        ui_callback: Optional[Callable[[str, str], None]] = None,
    ):
        """Initialize the error handler."""
        self.logger = logger or AutomationLogger()
        self.ui_callback = ui_callback
        self.error_count = 0
        self.max_errors = 10  # Prevent infinite error loops

    def handle_error(
        self,
        error: Exception,
        context: Optional[str] = None,
        show_ui: bool = True,
    ) -> None:
        """Handle an error with logging and optional UI feedback."""
        if self.error_count >= self.max_errors:
            self.logger.critical("Maximum error count reached, stopping error handling")
            return

        self.error_count += 1

        # Determine error type and severity
        if isinstance(error, AutomationError):
            category = error.category
            severity = error.severity
            message = error.message
            details = error.details
        else:
            category = ErrorCategory.UNKNOWN
            severity = ErrorSeverity.ERROR
            message = str(error)
            details = {"exception_type": type(error).__name__}

        # Log the error
        log_message = f"[{category.value}] {message}"
        if context:
            log_message = f"[{context}] {log_message}"

        if severity == ErrorSeverity.CRITICAL:
            self.logger.critical(log_message, **details)
        elif severity == ErrorSeverity.ERROR:
            self.logger.error(log_message, **details)
        elif severity == ErrorSeverity.WARNING:
            self.logger.warning(log_message, **details)
        else:
            self.logger.info(log_message, **details)

        # Show UI feedback if requested
        if show_ui and self.ui_callback:
            try:
                self.ui_callback(message, severity.value)
            except Exception as ui_error:
                self.logger.error(f"Failed to show UI error: {ui_error}")

        # Show system message box for critical errors
        if severity == ErrorSeverity.CRITICAL:
            try:
                messagebox.showerror(
                    "Critical Error",
                    f"{message}\n\nPlease check the logs for details.",
                )
            except Exception:
                pass  # Fallback if tkinter is not available

    def handle_function(self, func: Callable, *args, **kwargs) -> Optional[Any]:
        """Decorator-style function wrapper for error handling."""
        try:
            return func(*args, **kwargs)
        except Exception as error:
            self.handle_error(error, context=f"Function: {func.__name__}")
            return None

    def reset_error_count(self) -> None:
        """Reset the error count."""
        self.error_count = 0


# =============================================================================
# CONTEXT MANAGERS
# =============================================================================


class ErrorContext:
    """Context manager for error handling."""

    def __init__(
        self,
        error_handler: ErrorHandler,
        context: str,
        show_ui: bool = True,
        reraise: bool = False,
    ):
        """Initialize the error context."""
        self.error_handler = error_handler
        self.context = context
        self.show_ui = show_ui
        self.reraise = reraise

    def __enter__(self):
        """Enter the error context."""
        return self

    def __exit__(self, exc_type, exc_val, exc_tb):
        """Exit the error context."""
        if exc_val is not None:
            self.error_handler.handle_error(
                exc_val,
                context=self.context,
                show_ui=self.show_ui,
            )
            if self.reraise:
                return False  # Re-raise the exception
        return True  # Suppress the exception


# =============================================================================
# UTILITY FUNCTIONS
# =============================================================================


def safe_execute(
    func: Callable,
    *args,
    error_handler: Optional[ErrorHandler] = None,
    context: Optional[str] = None,
    **kwargs,
) -> Optional[Any]:
    """Safely execute a function with error handling."""
    if error_handler is None:
        error_handler = ErrorHandler()

    try:
        return func(*args, **kwargs)
    except Exception as error:
        error_handler.handle_error(error, context=context)
        return None


def validate_condition(
    condition: bool,
    message: str,
    error_handler: Optional[ErrorHandler] = None,
) -> bool:
    """Validate a condition and handle errors."""
    if not condition:
        error = ValidationError(message)
        if error_handler:
            error_handler.handle_error(error)
        return False
    return True


def require_not_none(
    value: Any,
    name: str,
    error_handler: Optional[ErrorHandler] = None,
) -> bool:
    """Require that a value is not None."""
    return validate_condition(
        value is not None,
        f"{name} cannot be None",
        error_handler,
    )


def require_type(
    value: Any,
    expected_type: type,
    name: str,
    error_handler: Optional[ErrorHandler] = None,
) -> bool:
    """Require that a value is of a specific type."""
    return validate_condition(
        isinstance(value, expected_type),
        f"{name} must be of type {expected_type.__name__}, got {type(value).__name__}",
        error_handler,
    )


# =============================================================================
# GLOBAL INSTANCES
# =============================================================================

# Global logger and error handler instances
logger = AutomationLogger()
error_handler = ErrorHandler(logger)


# Convenience functions
def log_info(message: str, **kwargs) -> None:
    """Log info message."""
    logger.info(message, **kwargs)


def log_warning(message: str, **kwargs) -> None:
    """Log warning message."""
    logger.warning(message, **kwargs)


def log_error(message: str, **kwargs) -> None:
    """Log error message."""
    logger.error(message, **kwargs)


def log_critical(message: str, **kwargs) -> None:
    """Log critical message."""
    logger.critical(message, **kwargs)


def handle_error(
    error: Exception,
    context: Optional[str] = None,
    show_ui: bool = True,
) -> None:
    """Handle an error."""
    error_handler.handle_error(error, context, show_ui)


def safe_call(
    func: Callable,
    *args,
    context: Optional[str] = None,
    **kwargs,
) -> Optional[Any]:
    """Safely call a function with error handling."""
    return safe_execute(
        func,
        *args,
        error_handler=error_handler,
        context=context,
        **kwargs,
    )
