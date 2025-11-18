# Python-Specific Configuration

**IMPORTANT**: This file contains team-wide Python coding standards and is committed to version control. All team members should follow these standards. For personal preferences or local development overrides, create a `CLAUDE.local.md` file (gitignored, not tracked in version control).

This file contains Python-specific coding standards and best practices. These supplement the language-agnostic rules in CLAUDE.md.

## Naming Conventions

- Use camelCase for variable, function, and method names
- Use PascalCase for class names
- Use UPPER_CASE for constants and environment variables
- Use all lower-case filenames (with no underscores) composed of (at most) a three word description of the purpose of the file

## Python Syntax and Features

- Use Python 3.11 syntax and features
- Do not use type hints from the typing module unless needed for a dataclass

## Formatting and Style

- Follow the style guide of the Black project except where it conflicts with rules in CLAUDE.md or this file
- Use two spaces for indentation (not tabs)
- Wrap lines at 120 characters
- Do NOT leave space characters at the end of a line

## Code Quality & Linting

- **Run `spacing` linter first** to ensure blank line consistency (if not installed, then run `pip install spacing`)
- **Run `ruff check` and `ruff format`** to ensure code quality (if not installed, then run `pip install ruff`)
- Follow ruff configuration settings in `pyproject.toml` in the git repo root
- Common ruff violations to avoid:
  - E722: Use specific exception types, not bare `except:`
  - F401: Remove unused imports
  - E501: Line too long (follow 120 character limit)

## Project Structure

- Use `__init__.py` files for package initialization
- Use `__main__.py` file for executable packages (enables `python -m package_name`)
- Use pyproject.toml for Python dependency management instead of requirements.txt
- Follow PEP 621 standards for project metadata and dependency specification

## Virtual Environment

- Use virtual environment `.venv` in the git repo root for Python changes

## Quotes and Strings

- Use single quotes for strings
- Use triple double quotes for docstrings

## Imports

- Use explicit imports and not wildcard imports
- Use absolute imports and not relative imports
- Keep imports at the top of a function, method, or file

## Documentation

- Include reST style docstrings for all functions and classes
- Use `type` and `rtype` annotations in docstrings

Example:
```python
def calculateTotal(items):
  """
  Calculate the total price of items.

  :type items: list
  :param items: List of items with price attributes
  :rtype: float
  :return: Total price of all items
  """
  return sum(item.price for item in items)
```

## Unit Tests

- Use the filename `test_foo.py` for the `foo.py` module
- Put all unit test files in a `test/` subdirectory with a structure that models the project structure
  - For example: core/foo.py => test/core/test_foo.py
- Write unit tests using pytest and mocker
- Always run tests using `pytest` (not `python -m pytest`)
- Override the rule for function names in the test suite for functions that are a test function:
  - use a prefix `test_` followed by a suffix in camelCase describing the purpose of the test
    - For example: `test_checkForInvalidCeId` or `test_auditFeatureFileAssociationNoIssues`
- When fixing tests, only run the failing tests during iteration

## Testing Best Practices

- Prefer short, to-the-point tests that test situations corresponding to a single use case
- Do not call private methods directly inside unit tests
- Never mock methods of the class under test
- Use mocks only when necessary, for example:
  - when using a third-party interface (e.g, an API call) **always** use a mock
  - when natural set up would be too difficult (e.g., a race condition)
