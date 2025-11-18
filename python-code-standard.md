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

## End-to-End Testing with Playwright

### When to Use Playwright

Use Playwright for end-to-end (E2E) testing of web applications:
- Testing complete user flows through the browser (login, checkout, workflows)
- Validating UI interactions and visual behavior
- Cross-browser compatibility testing (Chromium, Firefox, WebKit)
- Testing JavaScript-heavy applications where DOM manipulation is critical

**Do not use Playwright for:**
- Unit tests of business logic (use pytest instead)
- API testing without UI (use requests or httpx)
- Performance testing (use specialized tools)

### Installation and Setup

**Step 1: Install Python package**
```bash
pip install pytest-playwright
```

**Step 2: Install browser binaries** (required!)
```bash
playwright install
```

**Add to dependencies** in `pyproject.toml`:
```toml
[tool.poetry.dependencies]
pytest = "^8.3.4"
pytest-playwright = "^0.6.2"
```

Or in `requirements.txt`:
```
pytest>=7.4.3
pytest-playwright>=0.4.3
```

### Test Organization

**Directory Structure**

Place Playwright E2E tests in a separate directory from unit tests:

```
project/
├── src/                    # Source code
├── tests/                  # Unit tests
│   ├── test_models.py
│   └── test_services.py
├── tests/e2e/             # E2E tests (recommended)
│   ├── test_login.py
│   ├── test_checkout.py
│   └── conftest.py        # Shared fixtures
└── pyproject.toml
```

Alternative structure (top-level e2e directory):
```
project/
├── src/
├── tests/                  # Unit tests only
├── e2e/                    # E2E tests
│   ├── test_login.py
│   └── conftest.py
└── pyproject.toml
```

**Why separate directories?**
- E2E tests are slower than unit tests
- Different test scope and purpose
- Allows running unit tests separately for fast feedback
- Clear separation of concerns

**Test File Naming**

Follow pytest conventions:
- File names: `test_*.py` (e.g., `test_login.py`, `test_checkout.py`)
- Test functions: `def test_*` (e.g., `def test_successful_login(page):`)

### Running E2E Tests

Use the existing `/test` command with directory path:

```bash
# Run all E2E tests
/test tests/e2e/

# Or if using top-level e2e/ directory
/test e2e/

# Run specific E2E test file
/test tests/e2e/test_login.py

# Run specific test function
/test tests/e2e/test_login.py::test_successful_login
```

**Using pytest directly** (for Playwright-specific options):
```bash
# Run with visible browser (headed mode)
pytest tests/e2e/ --headed

# Run with specific browser
pytest tests/e2e/ --browser firefox
pytest tests/e2e/ --browser webkit

# Run with multiple browsers
pytest tests/e2e/ --browser chromium --browser firefox

# Run with screenshots on failure
pytest tests/e2e/ --screenshot only-on-failure

# Run with tracing (for debugging)
pytest tests/e2e/ --tracing on

# Slow motion for debugging (milliseconds)
pytest tests/e2e/ --headed --slowmo 1000
```

### Configuration

**pytest.ini** (optional, for default Playwright options):
```ini
[pytest]
# Separate E2E tests from unit tests
testpaths = tests

# Playwright default options (applies to all E2E tests)
addopts =
    --browser chromium
    --screenshot only-on-failure
```

**conftest.py** (for custom fixtures):
```python
import pytest

@pytest.fixture(scope='session')
def browser_context_args(browser_context_args):
  """Customize browser context for all tests."""
  return {
    **browser_context_args,
    'viewport': {
      'width': 1920,
      'height': 1080,
    },
    'ignore_https_errors': True,
  }

@pytest.fixture(scope='session')
def browser_type_launch_args(browser_type_launch_args):
  """Customize browser launch options."""
  return {
    **browser_type_launch_args,
    'headless': False,  # Run headed by default
  }
```

### Test Structure and Patterns

**Basic Test Example**:
```python
from playwright.sync_api import Page, expect

def test_successful_login(page: Page):
  """Test user can login with valid credentials."""
  page.goto('https://example.com/login')
  page.get_by_label('Username').fill('testuser')
  page.get_by_label('Password').fill('password123')
  page.get_by_role('button', name='Login').click()

  # Playwright auto-waits for elements
  expect(page).to_have_url(re.compile(r'.*/dashboard'))
  expect(page.get_by_text('Welcome')).to_be_visible()
```

**Page Object Pattern** (recommended for maintainability):

`pages/login_page.py`:
```python
from playwright.sync_api import Page

class LoginPage:
  def __init__(self, page: Page):
    self.page = page
    self.username_input = page.get_by_label('Username')
    self.password_input = page.get_by_label('Password')
    self.login_button = page.get_by_role('button', name='Login')

  def navigate(self):
    self.page.goto('https://example.com/login')

  def login(self, username: str, password: str):
    self.username_input.fill(username)
    self.password_input.fill(password)
    self.login_button.click()
```

`tests/e2e/test_login.py`:
```python
import pytest
from playwright.sync_api import Page
from pages.login_page import LoginPage

@pytest.fixture
def login_page(page: Page):
  return LoginPage(page)

def test_login_with_page_object(login_page):
  """Test login using Page Object pattern."""
  login_page.navigate()
  login_page.login('testuser', 'password123')
  # Assert successful login...
```

### Best Practices

**Fixtures and Isolation**
- Use `page` fixture provided by pytest-playwright (function scope, isolated per test)
- Each test gets a fresh browser context and page
- No shared state between tests

**API vs Sync**
- **Always use sync API** with pytest-playwright (not async/await)
- Import from `playwright.sync_api`, not `playwright.async_api`

**Locators**
- Prefer role-based locators: `page.get_by_role('button', name='Submit')`
- Use label-based locators: `page.get_by_label('Email')`
- Use text-based locators: `page.get_by_text('Welcome')`
- Avoid CSS selectors when possible (more brittle)

**Auto-Waiting**
- Playwright auto-waits for elements to be actionable
- Avoid manual `time.sleep()` - use `page.wait_for_selector()` if needed
- Use `expect()` for assertions with built-in waiting

**Test Organization**
- One test per user scenario
- Keep tests focused and independent
- Use Page Objects for complex pages
- Share setup via fixtures in `conftest.py`

**Debugging**
- Run with `--headed` to see browser
- Use `--slowmo 1000` to slow down actions
- Use `page.pause()` to pause execution and inspect
- Enable `--tracing on` to record test execution

**Performance**
- E2E tests are slower - keep suite manageable
- Run E2E tests separately from unit tests
- Consider parallel execution: `pytest tests/e2e/ -n auto` (requires pytest-xdist)
- Mock external APIs when possible to improve speed

### Common Issues

**Browser binaries not found**
```
Error: "chromium" browser was not found
```
**Solution**: Run `playwright install` after installing package

**Virtual environment path issues**

If browsers installed globally but script runs in venv:
```bash
# Install browsers in virtual environment
PLAYWRIGHT_BROWSERS_PATH=0 playwright install
```

**Timeout errors**

If pages load slowly:
```python
# Increase timeout for specific operation
page.goto('https://example.com/', timeout=60000)  # 60 seconds

# Or set default timeout
page.set_default_timeout(30000)  # 30 seconds
```

**Tests are flaky**

Causes: Race conditions, network timing, element availability

**Solutions**:
- Use Playwright's auto-waiting (built-in)
- Use proper locators (`get_by_role`, `get_by_label`)
- Avoid `time.sleep()`, use `wait_for_selector()` instead
- Use `expect()` assertions with built-in retry logic
