# 🤝 Contributing to AgentSpec

Thank you for your interest in contributing! This document provides guidelines for contributing to the AgentSpec framework. Because AgentSpec operates on the ethos of rigid deterministic behavior, we prioritize robust assertions, exhaustive unit tests, and rigorous edge-case handling.

## 🛠 Development Setup

1. **Fork and clone the repository:**
```bash
git clone https://github.com/agentcontract/agentcontract.git
cd agentcontract
```

2. **Create a virtual environment:**
```bash
python -m venv venv
source venv/bin/activate  # On Windows: venv\Scripts\activate
```

3. **Install in comprehensive development mode:**
```bash
pip install -e ".[dev,all]"
```

4. **Install asynchronous testing modules (if missing):**
```bash
pip install pytest-asyncio
```

---

## 🎨 Code Style

We mandate strict adherence to pythonic best practices and utilize the following automated toolchain:
- **ruff** for high-performance linting and import sorting.
- **black** for PEP8 standard code formatting.
- **mypy** for strict static type checking.

Always ensure the following passes before committing your branch:
```bash
ruff check .
black --check .
mypy agentcontract/
```

---

## 🧪 Testing

Given that AgentSpec is a testing framework, we place heavy emphasis on testing the tester itself. All tests leverage `pytest`.

*Run the test suite (synchronous and asynchronous):*
```bash
pytest tests/ -v
```

*Run with explicit coverage analysis:*
```bash
pytest tests/ --cov=agentcontract
```

---

## 🔥 Adding New Features

### 1. Adding a New Framework Adapter

1. Create a new file in `agentcontract/adapters/` (e.g., `gemini.py`)
2. Inherit cleanly from `BaseAdapter`.
3. Implement `run()` for synchronous workflows and `arun()` for asynchronous.
4. Add verification tests in `tests/`.
5. Update `README.md` and `getting-started.md` adapter sections.

**Example implementation skeleton:**
```python
from agentcontract.adapters.base import BaseAdapter

class MyAdapter(BaseAdapter):
    def run(self, agent, input, context=None):
        # Intercept and rigidly record tool calls locally
        self._interceptor.record("tool_name", args, result)
        return result
        
    async def arun(self, agent, input, context=None):
        return await agent(...)
```

### 2. Adding New Assertions

Assertions are segmented into standalone handlers within `agentcontract/assertions/`.

To add a new assertion metric:
1. Define the boolean logic within the relevant assertion file (e.g. `agentcontract/assertions/count_assertions.py`).
2. Add the tracking method to `AgentResult`, `ToolAssertion`, or `CountAssertion` in `result.py` wrapping the newly implemented standalone method.
3. Throw rigorous exceptions on failure.

**Always ensure your PRs include:**
- Clear deterministic error messages (`ContractViolation`, `ArgMismatch`, etc.)
- Explicit python generic type hints.
- Extensive docstrings.
- Testing proving both failure triggers and assertion successes.

---

## 📫 Pull Request Process

1. **Create a branch**: `git checkout -b feature/my-feature`
2. **Make your changes** with atomic, functional commits.
3. **Add tests** for new functionality.
4. **Update documentation** wherever applicable.
5. **Run the test suite** locally.
6. **Submit a PR** mapping back to the initial Issue (if applicable).

### Commit Message Format

Use classic conventional commits to keep traces clean:
- `feat: add async chaos failure`
- `fix: resolve multi-agent arg parsing`
- `docs: update API pipeline docs`
- `test: added rate-limit edge cases`

---

## 📝 License

By contributing to AgentSpec, you agree that your contributions will be explicitly licensed under the MIT License.
