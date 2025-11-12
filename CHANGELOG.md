# Changelog

## [0.7.3] - 2025-11-12

- Fixed PEP 8 compliance: Comments after module-level definitions now correctly get 2 blank lines

## [0.7.2] - 2025-11-10

**Professional Project Infrastructure**

- **README badges**: Added pipeline status, coverage, PyPI version, Python versions, and license badges
- **Community files**: Added CONTRIBUTING.md with comprehensive contribution guidelines
- **Security policy**: Added SECURITY.md with vulnerability reporting process and security best practices
- **Issue templates**: Added structured bug report and feature request templates for GitLab
- **MR template**: Simplified merge request template for easier use
- **Dogfooding**: Added `lint:spacing` CI job - spacing now enforces its own blank line rules on itself
- **CI/CD pipeline**: Complete GitLab CI/CD with automated testing, coverage reporting, tagging, and PyPI publishing
- **Setup guide**: Added PYPI_SETUP.md with detailed instructions for automated publishing

## [0.7.1] - 2025-11-10

**CI/CD Enhancements**

- **Automated tagging**: Pipeline automatically creates git tags when version in `pyproject.toml` changes on main branch
- **Automated PyPI publishing**: When a version tag is created, pipeline automatically publishes to PyPI (requires PyPI credentials in GitLab CI/CD variables)
- **Complete automation**: Just bump version in `pyproject.toml` and push to main - tagging and publishing happen automatically
- See `PYPI_SETUP.md` for setup instructions

## [0.7.0] - 2025-11-10

**NEW FEATURE: Smart Path Discovery with Exclusions**

- **Automatic file discovery**: Running `spacing` without arguments now automatically discovers and formats all `.py` files in the current directory (recursively)
- **Smart default exclusions**: Automatically excludes common directories that shouldn't be formatted:
  - All hidden directories (starting with `.`)
  - Virtual environments: `venv`, `env`, `virtualenv`
  - Build artifacts: `build`, `dist`, `__pycache__`, `*.egg-info`, `*.egg`
- **Configurable exclusions**: New `[paths]` section in `spacing.toml` allows custom exclusions:
  - `exclude_names`: List of directory/file names to exclude
  - `exclude_patterns`: List of glob patterns to exclude
  - `include_hidden`: Override default hidden directory exclusion
- **Explicit path override**: Exclusions only apply during automatic discovery; explicitly provided paths bypass all exclusions
- **New module**: Added `pathfilter.py` for path discovery and filtering logic

## [0.6.1] - 2025-11-10

- Removed redundant `__version__` from `__init__.py` (version now only in pyproject.toml)
- Added Python 3.13 and 3.14 support
- Updated development status to Production/Stable

## [0.6.0] - 2025-11-10

**BREAKING CHANGE: Project Renamed**
- Renamed project from `prism-blanklines` to `spacing`
- Command line tool renamed from `prism` to `spacing`
- Package now available on PyPI as `spacing` instead of `prism-blanklines`
- Repository moved to GitLab: https://gitlab.com/oldmission/spacing
- All imports changed from `prism.*` to `spacing.*`
- Configuration file renamed from `prism.toml` to `spacing.toml`

## [0.5.6] - 2025-11-09

- Fixed `async with` and `async for` being misclassified as function calls
  - `async with self.lock:` now correctly classified as CONTROL instead of CALL
  - `async for item in queue:` now correctly classified as CONTROL instead of CALL
  - This was causing blank lines to be incorrectly added at the start of `async with` scopes
  - Updated CONTROL pattern to include optional `async` prefix for control flow keywords

## [0.5.5] - 2025-11-09

- Fixed method calls with lambda keyword arguments being misclassified as assignments
  - `output[STUDY].sort(key=lambda k: k[SDATE])` now correctly classified as CALL instead of ASSIGNMENT
  - Enhanced early function call detection to support subscript access patterns
  - Uses `]` or `)` followed by `=` to distinguish assignments from method calls with keyword arguments
  - Prevents incorrect blank lines being added between consecutive method calls with lambdas

## [0.5.4] - 2025-11-09

- Fixed dictionary assignments with special characters in string keys being misclassified as function calls
  - `response.headers['Access-Control-Allow-Origin'] = allowedOrigin` now correctly classified as ASSIGNMENT instead of CALL
  - Proactively added common special characters to ASSIGNMENT pattern: `-`, `:`, `/`, `+`, `&`, `?`, `;`, `@`, `#`, `%`, `*`, `|`
  - Handles URLs, file paths, email addresses, timestamps, and other string formats in dictionary keys
  - Intentionally excluded comparison operators (`!`, `<`, `>`) to avoid misclassifying comparisons as assignments
  - Prevents incorrect blank lines being added between consecutive assignments with special characters

## [0.5.3] - 2025-11-09

- Fixed dictionary assignments with f-strings and method calls being misclassified as function calls
  - `cookies[f'{VAR}_0'] = value` now correctly classified as ASSIGNMENT instead of CALL
  - `ctx.request.cookies[getApprovalCookieName()] = str(approval)` now correctly classified as ASSIGNMENT
  - Added `{}` and `()` to ASSIGNMENT pattern character class to handle f-strings and method calls
  - Moved FLOW_CONTROL before ASSIGNMENT in pattern precedence to prevent `return func()` being misclassified
  - Prevents incorrect blank lines being added between consecutive dictionary assignments

## [0.5.2] - 2025-11-09

- Fixed classifier misclassifying control statements with equals in string literals
  - `if 'CN=' in subject:` now correctly classified as CONTROL instead of ASSIGNMENT
  - Reordered PATTERNS dictionary so CONTROL comes before ASSIGNMENT (specific before general)
  - Prevents incorrect blank line removal between assignment and control statements
- Fixed `yield` with parentheses being misclassified as function call
  - `yield (Status.SUCCESS, None)` now correctly classified as FLOW_CONTROL instead of CALL
  - Added `return` and `yield` to controlKeywords exclusion list in early function call detection
  - Ensures consecutive yield statements don't get incorrect blank lines between them
- Reorganized test suite: moved all tests from test_bugs.py to appropriate module test files
  - Classifier tests → test_classifier.py
  - Rules tests → test_rules.py
  - Integration tests → test_integration.py
  - Nested scopes tests → test_nestedscopes.py
  - Analyzer tests → test_analyzer.py
  - Docstring tests → test_docstrings.py

## [0.5.1] - 2025-11-09

- Added new `BlockType.FLOW_CONTROL` for return and yield statements
  - `return` and `yield` (including `yield from`) now have their own block type
  - Separated from CALL block type to preserve blank lines before return/yield
  - Reflects coding practice where return/yield are treated as significant control flow statements
  - CLI now supports `flow_control` in `--blank-lines` configuration

## [0.5.0] - 2025-11-09

- Fixed control statements with parentheses being misclassified as function calls
  - `if (condition) and other:` now correctly classified as CONTROL instead of CALL
  - Prevents incorrect blank line additions after control statements
  - Ensures consecutive control blocks get proper blank line separation
  - Added exclusion list for control keywords in early function call detection

## [0.4.6] - 2025-11-09

- Fixed decorated class docstrings not always getting blank line after them
  - `_isClassDefinition()` now checks all lines in statement, not just first line
  - Handles classes with decorators (e.g., `@dataclass`) correctly
  - Class docstrings always get 1 blank line per PEP 257, regardless of `after_docstring` config

## [0.4.5] - 2025-11-09

- Enhanced comment paragraph separation: preserve blank lines directly adjacent to comments
  - Blank lines between comment blocks are now preserved (comment paragraphs)
  - Blank lines immediately before/after comments are preserved (user intent)
  - Scope boundaries still take precedence (no blank lines at start of scope)

## [0.4.4] - 2025-10-16

- Fixed parser incorrectly treating apostrophes in comments as string delimiters
  - Comments with contractions (e.g., "don't", "can't") were causing massive parsing failures
  - Parser now stops processing when it encounters '#' outside of strings
  - This bug caused entire files to be mis-parsed as single giant statements

## [0.4.3] - 2025-10-16

- Fixed consecutive `async def` test functions not getting proper PEP 8 spacing
  - Parser now correctly recognizes `async def` as ending a decorator sequence
  - Consecutive module-level async function definitions now properly separated by 2 blank lines

## [0.4.2] - 2025-10-16

- Fixed dictionary assignments with string keys being misclassified as CALL
  - `environ['KEY'] = value` now correctly classified as ASSIGNMENT
  - Prevents incorrect blank lines being added between consecutive dictionary assignments

## [0.4.1] - 2025-10-14

- Updated `--check` mode output to "All checks passed!" when no formatting changes needed (matches ruff style)
- Fixed `async def` being misclassified as CALL instead of DEFINITION
  - This was causing blank lines to be incorrectly added between `async def` and its docstring
  - Now properly recognizes `async def` as a function definition
- Fixed class docstrings always requiring 1 blank line before first method, regardless of `after_docstring` config
  - Class docstrings now always get 1 blank line (PEP 257 requirement)
  - Function/method docstrings respect the `after_docstring` configuration setting
  - Fixed comment handling in blank line calculation to properly use BlockType.COMMENT

## [0.4.0] - 2025-10-14

- Added configurable blank lines after docstrings via `after_docstring` configuration
  - Default: 1 blank line (PEP 257 compliance)
  - Set to 0 for compact style with no blank line after docstrings
  - Configurable via TOML (`after_docstring = 0`) or CLI (`--blank-lines-after-docstring 0`)
- Fixed module-level config imports to use JIT (just-in-time) imports for runtime configuration changes

## [0.3.0] - 2025-10-05

**BREAKING CHANGES**: Full PEP 8 and PEP 257 compliance

- **PEP 8 Definition Spacing**: Scope-aware blank lines between function/class definitions
  - **2 blank lines** between top-level (module level) function/class definitions
  - **1 blank line** between method definitions inside classes (nested levels)
  - Automatically detects indentation level to apply correct spacing

- **PEP 257 Docstring Spacing**: Blank lines after docstrings follow normal block transition rules
  - Blank line required after docstrings before first statement (per PEP 257)
  - Removed special suppression of blank lines after docstrings in function/class bodies
  - Aligns with Ruff's formatting expectations for docstring spacing

## [0.2.1] - 2025-01-26

- Added `--quiet` flag to suppress all output except errors
- Fixed missing Statement import in rules.py

## [0.2.0] - 2025-01-26

- Added configurable indent width detection (default 2 spaces, configurable via `indent_width`)
- Added atomic file operations with temporary files for safer processing
- Added CLI `--dry-run` flag to preview changes without applying them
- Added CLI `--verbose` flag for detailed processing information
- Added specific exception handling for file operations (encoding, permissions, I/O errors)
- Implemented singleton configuration pattern for cleaner code architecture
- Added pre-compiled regex patterns for improved performance
- Added end-of-file newline preservation to maintain existing file formatting
- Renamed `tab_width` to `indent_width` for clarity (breaking change)
- Major code quality improvements and critical issue fixes

## [0.1.3] - 2025-01-09

- Fixed blank lines being incorrectly added after multi-line docstrings in function bodies

## [0.1.2] - 2025-01-09

- Fixed blank lines being removed between consecutive class methods
- Added --version flag to display version from pyproject.toml
- Fixed blank lines after docstrings in function bodies
- Fixed internal blank lines being removed from multi-line docstrings
- Fixed comment block "leave-as-is" behavior for blank line preservation

## [0.1.1] - 2025-01-09

- Initial release
