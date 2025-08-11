# Contributing to Prompt Stacker

Thank you for your interest in contributing to Prompt Stacker! This document provides guidelines and information for contributors.

## 🚀 Getting Started

### Prerequisites

- Python 3.8 or higher
- Git
- A GitHub account

### Setting Up the Development Environment

1. **Fork the repository**
   ```bash
   # Clone your fork
   git clone https://github.com/yourusername/prompt-stacker.git
   cd prompt-stacker
   ```

2. **Create a virtual environment**
   ```bash
   python -m venv venv
   source venv/bin/activate  # On Windows: venv\Scripts\activate
   ```

3. **Install dependencies**
   ```bash
   pip install -r requirements.txt
   pip install -r requirements-dev.txt  # Development dependencies
   ```

4. **Install pre-commit hooks**
   ```bash
   pre-commit install
   ```

## 🛠️ Development Workflow

### Code Style

We use the following tools to maintain code quality:

- **Black**: Code formatting
- **Flake8**: Linting
- **isort**: Import sorting
- **pre-commit**: Git hooks

### Running Tests

```bash
# Run all tests
pytest

# Run with coverage
pytest --cov=. --cov-report=html

# Run specific test file
pytest tests/test_automator.py
```

### Code Formatting

```bash
# Format code with Black
black .

# Sort imports
isort .

# Check formatting
black --check .
isort --check-only .
```

## 📝 Making Changes

### Branch Naming

Use descriptive branch names:
- `feature/add-new-timer-option`
- `bugfix/fix-coordinate-capture`
- `docs/update-readme`

### Commit Messages

Follow conventional commit format:
```
type(scope): description

[optional body]

[optional footer]
```

Types:
- `feat`: New feature
- `fix`: Bug fix
- `docs`: Documentation changes
- `style`: Code style changes
- `refactor`: Code refactoring
- `test`: Test changes
- `chore`: Maintenance tasks

### Pull Request Process

1. **Create a feature branch** from `main`
2. **Make your changes** following the coding standards
3. **Write/update tests** for new functionality
4. **Update documentation** if needed
5. **Run tests** locally
6. **Submit a pull request** with a clear description

### Pull Request Template

```markdown
## Description
Brief description of changes

## Type of Change
- [ ] Bug fix
- [ ] New feature
- [ ] Documentation update
- [ ] Code refactoring
- [ ] Other (please describe)

## Testing
- [ ] Tests pass locally
- [ ] Added new tests for new functionality
- [ ] Updated existing tests

## Checklist
- [ ] Code follows style guidelines
- [ ] Self-review completed
- [ ] Documentation updated
- [ ] No breaking changes
```

## 🐛 Reporting Issues

### Bug Reports

When reporting bugs, please include:

1. **Environment details**:
   - OS and version
   - Python version
   - Package versions

2. **Steps to reproduce**:
   - Clear, step-by-step instructions
   - Expected vs actual behavior

3. **Additional context**:
   - Screenshots if applicable
   - Error messages/logs
   - Relevant configuration

### Feature Requests

For feature requests:

1. **Describe the feature** clearly
2. **Explain the use case** and benefits
3. **Provide examples** if possible
4. **Consider implementation** complexity

## 📚 Documentation

### Code Documentation

- Use docstrings for all public functions and classes
- Follow Google or NumPy docstring format
- Include type hints where appropriate

### User Documentation

- Update README.md for user-facing changes
- Add examples and usage instructions
- Keep installation and setup instructions current

## 🔧 Development Tools

### Pre-commit Hooks

We use pre-commit hooks to ensure code quality:

```bash
# Install pre-commit
pip install pre-commit

# Install hooks
pre-commit install

# Run manually
pre-commit run --all-files
```

### IDE Configuration

Recommended VS Code settings:

```json
{
    "python.formatting.provider": "black",
    "python.linting.enabled": true,
    "python.linting.flake8Enabled": true,
    "editor.formatOnSave": true,
    "editor.codeActionsOnSave": {
        "source.organizeImports": true
    }
}
```

## 🎯 Areas for Contribution

### High Priority
- Bug fixes
- Performance improvements
- UI/UX enhancements
- Documentation improvements

### Medium Priority
- New automation features
- Additional theme options
- Export/import functionality
- Plugin system

### Low Priority
- Additional prompt templates
- Advanced configuration options
- Integration with other tools

## 📞 Getting Help

- **Issues**: Use GitHub Issues for bugs and feature requests
- **Discussions**: Use GitHub Discussions for questions and ideas
- **Code Review**: All PRs will be reviewed by maintainers

## 📄 License

By contributing to Prompt Stacker, you agree that your contributions will be licensed under the MIT License.

---

Thank you for contributing to Prompt Stacker! 🚀
