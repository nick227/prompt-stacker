# Testing Strategy for Cursor Automation System

This document outlines the comprehensive testing strategy implemented for the Cursor Automation System, including unit tests, integration tests, and testing best practices.

## Table of Contents

1. [Testing Architecture](#testing-architecture)
2. [Test Organization](#test-organization)
3. [Running Tests](#running-tests)
4. [Test Categories](#test-categories)
5. [Test Coverage](#test-coverage)
6. [Best Practices](#best-practices)
7. [Continuous Integration](#continuous-integration)

## Testing Architecture

### Overview

The testing architecture follows a **service-oriented testing approach** that mirrors the application's modular design:

```
tests/
├── conftest.py                    # Shared fixtures and configuration
├── test_prompt_editor_service.py  # Prompt editor business logic
├── test_coordinate_service.py     # Coordinate capture functionality
├── test_countdown_service.py      # Countdown timer logic
├── test_file_service.py          # File parsing and saving
├── test_automator.py             # Core automation functionality
└── __init__.py                   # Test package initialization
```

### Key Principles

1. **Service Isolation**: Each service is tested independently with mocked dependencies
2. **Comprehensive Coverage**: All public methods and edge cases are tested
3. **Mock Strategy**: External dependencies (UI, file system, automation libraries) are mocked
4. **Test Data Management**: Fixtures provide consistent test data across test files
5. **Error Handling**: Both success and failure scenarios are thoroughly tested

## Test Organization

### Test Structure

Each test file follows a consistent structure:

```python
"""
Unit tests for [ServiceName]

Tests the [specific functionality] and [business logic].
"""

import pytest
from unittest.mock import Mock, patch, MagicMock
from [service_module] import [ServiceClass]

class Test[ServiceClass]:
    """Test cases for [ServiceClass]."""
    
    @pytest.fixture
    def service(self):
        """Create a fresh service instance for each test."""
        return [ServiceClass]()
    
    @pytest.mark.unit
    def test_method_success(self, service):
        """Test successful method execution."""
        # Arrange
        # Act
        # Assert
```

### Test Categories

Tests are categorized using pytest markers:

- `@pytest.mark.unit`: Pure unit tests with mocked dependencies
- `@pytest.mark.integration`: Integration tests with real dependencies
- `@pytest.mark.slow`: Tests that take longer to execute
- `@pytest.mark.ui`: Tests requiring UI components
- `@pytest.mark.automation`: Tests related to automation functionality

## Running Tests

### Quick Start

```bash
# Run all tests (excluding slow tests)
python run_tests.py

# Run with coverage report
python run_tests.py --coverage

# Run only unit tests
python run_tests.py --unit

# Run specific test file
python run_tests.py --test-file test_prompt_editor_service.py

# Run specific test function
python run_tests.py --test-function test_load_prompts_success

# Run with verbose output
python run_tests.py --verbose
```

### Using pytest directly

```bash
# Run all tests
pytest tests/

# Run with coverage
pytest tests/ --cov=src --cov-report=html

# Run specific test file
pytest tests/test_prompt_editor_service.py

# Run tests matching pattern
pytest tests/ -k "prompt"

# Run tests with specific marker
pytest tests/ -m "unit"
```

## Test Categories

### 1. Unit Tests

**Purpose**: Test individual components in isolation with mocked dependencies.

**Coverage**:
- Service initialization and state management
- Method parameter validation
- Business logic execution
- Error handling and edge cases
- Return value validation

**Example**:
```python
@pytest.mark.unit
def test_load_prompts_success(self, service, sample_prompts):
    """Test successful prompt loading."""
    result = service.load_prompts(sample_prompts)
    
    assert result.success is True
    assert result.message == "Loaded 5 prompts"
    assert result.prompts == sample_prompts
```

### 2. Integration Tests

**Purpose**: Test component interactions with real dependencies.

**Coverage**:
- File system operations
- UI component interactions
- Service-to-service communication
- End-to-end workflows

**Example**:
```python
@pytest.mark.integration
def test_prompt_editor_ui_save_flow(self, temp_dir):
    """Test complete prompt editor save workflow."""
    # Test the full save flow from UI to file system
```

### 3. Mock Strategy

**External Dependencies Mocked**:
- `pyautogui`: Mouse and keyboard automation
- `pyperclip`: Clipboard operations
- `pynput`: Input monitoring
- `customtkinter`: UI components
- `tkinter`: GUI framework
- File system operations
- Time-based operations

**Mock Examples**:
```python
@pytest.fixture
def mock_pyautogui(self):
    """Mock pyautogui for testing."""
    with patch('automator.pyautogui') as mock_pag:
        mock_pag.click.return_value = None
        mock_pag.write.return_value = None
        yield mock_pag
```

## Test Coverage

### Current Coverage

The test suite provides comprehensive coverage for:

1. **PromptEditorService** (100% method coverage)
   - Prompt loading and validation
   - File operations (save/load)
   - CRUD operations (add/update/remove)
   - Error handling and edge cases

2. **CoordinateCaptureService** (100% method coverage)
   - Coordinate management
   - Mouse click capture
   - Validation and error handling
   - Persistence operations

3. **CountdownService** (100% method coverage)
   - Timer logic and state management
   - User control handling
   - Progress tracking
   - Callback management

4. **FileService** (100% method coverage)
   - File parsing (Python, text, CSV)
   - File saving in multiple formats
   - Error handling and validation
   - Directory management

5. **Automator** (100% method coverage)
   - Text pasting functionality
   - Button clicking with fallbacks
   - Automation flow control
   - Error recovery

### Coverage Reports

Generate coverage reports:

```bash
# Terminal coverage report
python run_tests.py --coverage

# HTML coverage report
pytest tests/ --cov=src --cov-report=html
# Open htmlcov/index.html in browser

# XML coverage report (for CI)
pytest tests/ --cov=src --cov-report=xml
```

## Best Practices

### 1. Test Naming

Use descriptive test names that explain the scenario:

```python
def test_load_prompts_with_invalid_file_path(self, service):
    """Test loading prompts with invalid file path."""
    
def test_coordinate_capture_with_mouse_right_click(self, service):
    """Test coordinate capture ignores right mouse clicks."""
```

### 2. Arrange-Act-Assert Pattern

Structure tests with clear sections:

```python
def test_method_success(self, service):
    """Test successful method execution."""
    # Arrange
    input_data = "test input"
    expected_result = "expected output"
    
    # Act
    result = service.method(input_data)
    
    # Assert
    assert result == expected_result
```

### 3. Fixture Usage

Use fixtures for common setup:

```python
@pytest.fixture
def sample_prompts(self):
    """Sample prompts for testing."""
    return [
        "This is a test prompt",
        "Another test prompt with 'quotes'",
        "Multi-line\nprompt with\nline breaks"
    ]
```

### 4. Error Testing

Test both success and failure scenarios:

```python
def test_method_success(self, service):
    """Test successful method execution."""
    result = service.method("valid_input")
    assert result.success is True

def test_method_failure(self, service):
    """Test method failure with invalid input."""
    result = service.method("invalid_input")
    assert result.success is False
    assert "error message" in result.message
```

### 5. Mock Verification

Verify that mocks are called correctly:

```python
def test_method_calls_dependency(self, service, mock_dependency):
    """Test that method calls dependency correctly."""
    service.method("input")
    
    mock_dependency.assert_called_once_with("input")
    mock_dependency.assert_called_with("input")
```

## Continuous Integration

### GitHub Actions

The project includes GitHub Actions for automated testing:

```yaml
name: Tests
on: [push, pull_request]
jobs:
  test:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v3
      - name: Set up Python
        uses: actions/setup-python@v4
        with:
          python-version: '3.9'
      - name: Install dependencies
        run: |
          pip install -r requirements-dev.txt
      - name: Run tests
        run: |
          python run_tests.py --coverage
      - name: Upload coverage
        uses: codecov/codecov-action@v3
```

### Pre-commit Hooks

Configure pre-commit hooks for code quality:

```yaml
# .pre-commit-config.yaml
repos:
  - repo: https://github.com/pre-commit/pre-commit-hooks
    rev: v4.4.0
    hooks:
      - id: trailing-whitespace
      - id: end-of-file-fixer
      - id: check-yaml
      - id: check-added-large-files
  - repo: https://github.com/psf/black
    rev: 23.3.0
    hooks:
      - id: black
  - repo: https://github.com/pycqa/flake8
    rev: 6.0.0
    hooks:
      - id: flake8
```

## Test Maintenance

### Adding New Tests

1. **Create test file**: `tests/test_new_service.py`
2. **Follow naming convention**: `TestNewService` class
3. **Add appropriate markers**: `@pytest.mark.unit`
4. **Include comprehensive coverage**: Success, failure, edge cases
5. **Update documentation**: Add to this file if needed

### Updating Existing Tests

1. **Maintain backward compatibility**: Don't break existing tests
2. **Update fixtures**: If shared data changes
3. **Review coverage**: Ensure new functionality is tested
4. **Update documentation**: Reflect any changes

### Test Data Management

- Use fixtures for consistent test data
- Create realistic test scenarios
- Include edge cases and error conditions
- Keep test data minimal but comprehensive

## Troubleshooting

### Common Issues

1. **Import Errors**: Ensure `src/` is in Python path
2. **Mock Issues**: Verify mock setup and teardown
3. **Test Isolation**: Use fresh fixtures for each test
4. **Timing Issues**: Mock time-based operations

### Debugging Tests

```bash
# Run single test with verbose output
pytest tests/test_file.py::TestClass::test_method -v -s

# Run with debugger
pytest tests/test_file.py --pdb

# Run with print statements
pytest tests/test_file.py -s
```

## Conclusion

This testing strategy provides:

- **Comprehensive Coverage**: All critical functionality is tested
- **Maintainable Tests**: Clear structure and documentation
- **Fast Execution**: Unit tests run quickly with mocked dependencies
- **Reliable Results**: Consistent test environment and data
- **Easy Debugging**: Clear error messages and test isolation

The test suite serves as both documentation and validation, ensuring the application remains reliable and maintainable as it evolves.
