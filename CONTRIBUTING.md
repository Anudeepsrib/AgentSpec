# Contributing to agentcontract

Thank you for your interest in contributing! This document provides guidelines for contributing to agentcontract.

## Development Setup

1. Fork and clone the repository:
```bash
git clone https://github.com/yourusername/agentcontract.git
cd agentcontract
```

2. Create a virtual environment:
```bash
python -m venv venv
source venv/bin/activate  # On Windows: venv\Scripts\activate
```

3. Install in development mode:
```bash
pip install -e ".[dev,all]"
```

4. Install pre-commit hooks:
```bash
pre-commit install
```

## Code Style

We use:
- **ruff** for linting and import sorting
- **black** for code formatting
- **mypy** for type checking

Run checks before committing:
```bash
ruff check .
black --check .
mypy agentcontract/
```

## Testing

Run the test suite:
```bash
pytest tests/ -v
```

Run with coverage:
```bash
pytest tests/ --cov=agentcontract
```

## Adding New Features

### Adding a New Adapter

1. Create a new file in `agentcontract/adapters/`
2. Inherit from `BaseAdapter`
3. Implement the `run()` method
4. Add tests in `tests/test_adapters/`
5. Update documentation

Example:
```python
from agentcontract.adapters.base import BaseAdapter

class MyAdapter(BaseAdapter):
    def run(self, agent, input, context=None):
        # Intercept and record tool calls
        self._interceptor.record("tool_name", args, result)
        return result
```

### Adding New Assertions

Add assertion methods to:
- `AgentResult` for top-level assertions
- `ToolAssertion` for tool-specific assertions

Always include:
- Clear error messages with context
- Proper type hints
- Docstrings
- Tests

## Pull Request Process

1. **Create a branch**: `git checkout -b feature/my-feature`
2. **Make your changes** with clear commit messages
3. **Add tests** for new functionality
4. **Update documentation** as needed
5. **Run the test suite** to ensure nothing is broken
6. **Submit a PR** with a clear description

## Commit Message Format

Use conventional commits:
- `feat: add new assertion type`
- `fix: correct ordering bug`
- `docs: update API reference`
- `test: add chaos injector tests`

## Code Review

All PRs require review. Address feedback promptly and maintain a respectful tone.

## Questions?

- Open an issue for bugs or feature requests
- Start a discussion for questions
- Join our community chat

## License

By contributing, you agree that your contributions will be licensed under the MIT License.
