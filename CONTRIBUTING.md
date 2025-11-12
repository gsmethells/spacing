# Contributing to Spacing

Thank you for your interest in contributing to Spacing! This document provides guidelines for contributing to the project.

## Code of Conduct

We are committed to providing a welcoming and inclusive environment. Please be respectful and professional in all interactions.

## How to Contribute

### Reporting Bugs

Before submitting a bug report:
1. Check the [issue tracker](https://gitlab.com/oldmission/spacing/-/issues) to see if it's already reported
2. Ensure you're using the latest version of spacing
3. Verify the issue is reproducible

When submitting a bug report, include:
- **Clear title and description**
- **Steps to reproduce** the issue
- **Expected behavior** vs **actual behavior**
- **Python version** and **spacing version**
- **Minimal code example** that demonstrates the issue
- **Configuration file** (spacing.toml) if relevant

### Suggesting Features

Feature suggestions are welcome! Please:
1. Check if the feature already exists or has been requested
2. Explain the use case and why it would benefit users
3. Consider if it aligns with spacing's focus on blank line formatting
4. Be open to discussion about implementation approaches

### Pull Requests

#### Before You Start

1. **Discuss major changes** by opening an issue first
2. **Check existing merge requests** to avoid duplicate work
3. **Fork the repository** and create a feature branch

#### Development Setup

```bash
# Clone your fork
git clone https://gitlab.com/your-username/spacing.git
cd spacing

# Install in development mode
pip install -e .

# Install development dependencies
pip install pytest pytest-cov ruff
```

#### Making Changes

1. **Create a feature branch**:
   ```bash
   git checkout -b feature/your-feature-name
   ```

2. **Follow coding standards** (see below)

3. **Write tests** for your changes:
   - Add unit tests to the appropriate `test/test_*.py` file
   - Ensure all tests pass: `pytest test/`
   - Aim for high test coverage

4. **Update documentation**:
   - Update README.md if adding user-facing features
   - Update design.md for architectural changes
   - Add entry to CHANGELOG.md

5. **Run quality checks**:
   ```bash
   # Run tests
   PYTHONPATH=src pytest test/ -v

   # Check code quality
   ruff check src/spacing/ test/

   # Format code
   ruff format src/spacing/ test/

   # Format blank lines with spacing (dogfooding!)
   PYTHONPATH=src python -m spacing.cli

   # Check blank lines with spacing
   PYTHONPATH=src python -m spacing.cli --check

   # Check coverage
   PYTHONPATH=src pytest test/ --cov=spacing --cov-report=term-missing
   ```

6. **Commit your changes**:
   ```bash
   git add .
   git commit -m "Add feature: brief description"
   ```

#### Coding Standards

Spacing follows strict coding standards defined in `CLAUDE.md`. Key points:

**Python Style**:
- Use Python 3.11+ syntax
- Follow PEP 8 (enforced by ruff)
- Use single quotes for strings, triple double quotes for docstrings
- Line length: 120 characters maximum
- Indentation: 2 spaces (not tabs)

**Blank Lines** (yes, we dogfood our own tool!):
- Run `spacing` on your code before committing
- Follow the blank line rules defined in the project

**Naming Conventions**:
- `camelCase` for variables, functions, and methods
- `PascalCase` for class names
- `UPPER_CASE` for constants

**Documentation**:
- Include reST-style docstrings for all public functions and classes
- Document complex business logic with comments
- Use XXX comments for important implementation notes

**Testing**:
- Write tests for all bug fixes (regression tests)
- Write tests for all new features
- Test both success and failure scenarios
- Use descriptive test names: `test_featureDescription`

**Commits**:
- Write clear, descriptive commit messages
- Reference issue numbers when applicable
- Keep commits focused and atomic

#### Submitting Your Merge Request

1. **Push to your fork**:
   ```bash
   git push origin feature/your-feature-name
   ```

2. **Create a merge request** on GitLab:
   - Use a clear, descriptive title
   - Fill out the merge request template
   - Link to related issues
   - Describe what changed and why
   - Include test plan/verification steps

3. **Address review feedback**:
   - Respond to all comments
   - Make requested changes
   - Push updates to the same branch

4. **CI/CD pipeline must pass**:
   - All tests must pass
   - Code quality checks must pass
   - Coverage should not decrease

## Development Workflow

### Testing

```bash
# Run all tests
PYTHONPATH=src pytest test/ -v

# Run specific test file
PYTHONPATH=src pytest test/test_rules.py -v

# Run specific test
PYTHONPATH=src pytest test/test_rules.py::TestBlankLineRuleEngine::testCommentBreakRule -v

# Run with coverage
PYTHONPATH=src pytest test/ --cov=spacing --cov-report=html
# Open htmlcov/index.html to see coverage report
```

### Code Quality

```bash
# Check for issues
ruff check src/spacing/ test/

# Auto-fix issues
ruff check --fix src/spacing/ test/

# Format code
ruff format src/spacing/ test/
```

### Dogfooding: Running Spacing on Itself

We use spacing to format its own codebase! This ensures:
- Spacing follows its own rules
- The tool works on real-world code
- We catch bugs early

```bash
# Format the spacing codebase
PYTHONPATH=src python -m spacing.cli

# Check if formatting is needed (this runs in CI)
PYTHONPATH=src python -m spacing.cli --check

# The CI pipeline will fail if spacing's code doesn't follow spacing's rules!
```

## Project Structure

```
spacing/
├── src/spacing/          # Main package
│   ├── __init__.py
│   ├── analyzer.py       # Pass 1: File structure analysis
│   ├── classifier.py     # Statement classification
│   ├── cli.py            # Command-line interface
│   ├── config.py         # Configuration system
│   ├── parser.py         # Multiline statement parsing
│   ├── pathfilter.py     # Path discovery and filtering
│   ├── processor.py      # Pass 3: File I/O
│   ├── rules.py          # Pass 2: Blank line rules
│   └── types.py          # Core data structures
├── test/                 # Test suite
│   ├── test_analyzer.py
│   ├── test_classifier.py
│   ├── test_cli.py
│   ├── test_config.py
│   ├── test_integration.py
│   ├── test_parser.py
│   ├── test_pathfilter.py
│   ├── test_processor.py
│   ├── test_rules.py
│   └── test_types.py
├── design.md             # Architecture documentation
├── CLAUDE.md             # Detailed coding standards
└── pyproject.toml        # Project configuration
```

## Architecture Overview

Spacing uses a three-pass processing pipeline:

1. **Pass 1 (FileAnalyzer)**: Parses files into logical statements
2. **Pass 2 (BlankLineRuleEngine)**: Applies configurable blank line rules
3. **Pass 3 (FileProcessor)**: Writes formatted output atomically

See `design.md` for detailed architecture documentation.

## Getting Help

- **Questions**: Open a [discussion](https://gitlab.com/oldmission/spacing/-/issues) or issue
- **Bugs**: Report via [issue tracker](https://gitlab.com/oldmission/spacing/-/issues)
- **Security**: See SECURITY.md for reporting vulnerabilities

## License

By contributing to Spacing, you agree that your contributions will be licensed under the GPL-3.0-or-later license. See the LICENSE file for details.

## Recognition

All contributors will be acknowledged in the AUTHORS file.

Thank you for contributing to Spacing!
