# Contributing to AgentSpec

First off, thank you for considering contributing to AgentSpec! It's people like you that make AgentSpec such a great tool for the AI engineering community.

## Code of Conduct

By participating in this project, you agree to abide by our Code of Conduct (standard Contributor Covenant).

## How Can I Contribute?

### Reporting Bugs

- **Check the existing issues** to see if the bug has already been reported.
- If not, **open a new issue**. Include a clear title, a description of the problem, and steps to reproduce it.
- Include information about your environment (Python version, OS, AgentSpec version).

### Suggesting Enhancements

- **Open a new issue** with the tag "enhancement".
- Provide a clear and detailed explanation of the proposed feature.
- Explain why this feature would be useful to other users.

### Pull Requests

1. **Fork the repository** and create your branch from `main`.
2. **Install dependencies**: `pip install -e ".[dev,all]"`
3. **Write tests** for your changes. We aim for high coverage.
4. **Ensure the test suite passes**: `pytest tests/`
5. **Follow the style guide**: We use `ruff` for linting and `black` for formatting.
   - Run `ruff check .`
   - Run `black .`
6. **Update documentation**: If you're adding a feature or changing an API, update the relevant `.md` files in the `docs/` directory.
7. **Submit the PR** with a clear description of the changes and link to any relevant issues.

## Development Setup

We recommend using a virtual environment:

```bash
git clone https://github.com/Anudeepsrib/AgentSpec.git
cd AgentSpec
pip install -e ".[dev,all]"
pytest tests/
```

### Running Tests

```bash
# All tests
pytest tests/

# With coverage
pytest --cov=agentspec tests/
```

## Questions?

Feel free to open a discussion on GitHub or reach out to the maintainers.

Happy coding!
