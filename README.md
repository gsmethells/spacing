# Spacing

[![Pipeline Status](https://gitlab.com/oldmission/spacing/badges/main/pipeline.svg)](https://gitlab.com/oldmission/spacing/-/pipelines)
[![Coverage](https://gitlab.com/oldmission/spacing/badges/main/coverage.svg)](https://gitlab.com/oldmission/spacing/-/graphs/main/charts)
[![PyPI Version](https://img.shields.io/pypi/v/spacing.svg)](https://pypi.org/project/spacing/)
[![Python Versions](https://img.shields.io/pypi/pyversions/spacing.svg)](https://pypi.org/project/spacing/)
[![License: GPL v3](https://img.shields.io/badge/License-GPLv3-blue.svg)](https://www.gnu.org/licenses/gpl-3.0)

A Python code formatter that enforces configurable blank line rules.

## Overview

Spacing is a code formatting tool that intelligently manages blank lines in Python code, similar to how `black` handles code formatting. It applies sophisticated rules to ensure consistent spacing between different types of code blocks while preserving your code's logical structure and documentation.

## Features

- **Configurable blank line rules** - Customize spacing between different code block types
- **Smart block detection** - Identifies assignments, function calls, imports, control structures, definitions, and more
- **Multiline statement support** - Properly handles statements spanning multiple lines
- **Docstring preservation** - Never modifies content within docstrings
- **Nested scope handling** - Applies rules independently at each indentation level
- **Comment-aware processing** - Preserves existing spacing around comment blocks
- **Atomic file operations** - Safe file writing with automatic rollback on errors
- **Change detection** - Only modifies files that need formatting
- **Dry-run mode** - Preview changes without modifying files
- **Check mode** - Verify formatting without making changes

## Installation

### From PyPI

```bash
pip install spacing
```

### From Source

```bash
git clone git@gitlab.com:oldmission/spacing.git
cd spacing
pip install -e .
```

### Requirements

- Python 3.11 or higher
- No external dependencies for core functionality

## Quick Start

```bash
# Format all Python files in current directory (automatic discovery with smart exclusions)
spacing

# Format a single file
spacing myfile.py

# Format all Python files in a specific directory
spacing src/

# Check if files need formatting (exit 1 if changes needed)
spacing --check

# Preview changes without applying them
spacing --dry-run

# Show detailed processing information
spacing --verbose

# Show version
spacing --version
```

### Automatic File Discovery

When you run `spacing` without any path arguments, it automatically:
- Discovers all `.py` files in the current directory (recursively)
- Excludes common directories you don't want to format:
  - Hidden directories (starting with `.`)
  - Virtual environments (`venv`, `env`, `virtualenv`)
  - Build artifacts (`build`, `dist`, `__pycache__`, `*.egg-info`, `*.egg`)
- Respects custom exclusions defined in `spacing.toml` (see Configuration section below)

## Configuration

### Default Behavior

By default, spacing uses these rules (aligned with PEP 8):
- **1 blank line** between different block types
- **1 blank line** between consecutive control structures (`if`, `for`, `while`, `try`, etc.)
- **2 blank lines** between consecutive top-level (module level) function/class definitions
- **1 blank line** between consecutive method definitions inside classes
- **0 blank lines** between statements of the same type
  - Exception: **1 blank line** between consecutive control blocks at the same scope 

### Configuration File

Create a `spacing.toml` file in your project root to customize blank line rules:

```toml
[blank_lines]
# Default spacing between different block types (0-3 blank lines)
default_between_different = 1

# Spacing between consecutive control blocks (if, for, while, try, with)
consecutive_control = 1

# Spacing between consecutive definitions (def, class)
consecutive_definition = 1

# Indent width for indentation detection (default: 2 spaces)
indent_width = 2

# Fine-grained transition overrides
# Format: <from_block>_to_<to_block> = <count>
assignment_to_call = 2
call_to_assignment = 2
import_to_assignment = 0
control_to_definition = 2

[paths]
# Additional directory/file names to exclude during automatic discovery
exclude_names = ["my_generated_code", "legacy"]

# Glob patterns for more specific exclusions
exclude_patterns = ["**/old_*.py", "**/test_old_*.py"]

# Set to true to include hidden directories (overrides default exclusion)
include_hidden = false
```

**Note**: Path exclusions only apply when running `spacing` without arguments (automatic discovery). They are ignored when you explicitly specify paths like `spacing src/` or `spacing venv/` - this gives you full control when needed.

### Block Types

Spacing recognizes these code block types (in precedence order):

1. **`assignment`** - Variable assignments, list/dict comprehensions, lambda expressions
   ```python
   x = 42
   items = [i for i in range(10)]
   func = lambda x: x * 2
   ```

2. **`call`** - Function/method calls, `del`, `assert`, `pass`, `raise`, `yield`, `return`
   ```python
   print('hello')
   someFunction()
   return result
   ```

3. **`import`** - Import statements
   ```python
   import os
   from pathlib import Path
   ```

4. **`control`** - Control structures (`if`/`elif`/`else`, `for`/`else`, `while`/`else`, `try`/`except`/`finally`, `with`)
   ```python
   if condition:
       x = 1
       y = 0

   for item in items:
       prologue(item)
       process(item)
       epilogue(item)

   ```

5. **`definition`** - Function and class definitions
   ```python
   def myFunction():
       pass

   class MyClass:
       pass
   ```

6. **`declaration`** - `global` and `nonlocal` statements
   ```python
   global myVar
   nonlocal count
   ```

7. **`comment`** - Comment lines
   ```python
   # This is a comment
   ```

### Configuration Examples

#### Minimal spacing (compact style)
```toml
[blank_lines]
default_between_different = 0
consecutive_control = 1
consecutive_definition = 1
```

#### Extra spacing (airy style)
```toml
[blank_lines]
default_between_different = 2
consecutive_control = 2
consecutive_definition = 2
```

#### Custom transitions
```toml
[blank_lines]
# Default: 1 blank line between different types
default_between_different = 1

# But no blank lines between imports and assignments
import_to_assignment = 0

# And 2 blank lines between import blocks and definitions such as a `class`
import_to_definition = 2
```

### Using Custom Configuration

```bash
# Use a specific config file
spacing --config custom.toml myfile.py

# Use default configuration (ignore spacing.toml if it exists)
spacing --no-config myfile.py
```

## Block Classification Rules

### Precedence

When a statement could match multiple block types, spacing uses precedence:

```python
x = someFunction()  # Assignment (precedence over Call)
result = [i for i in range(10)]  # Assignment (comprehension)
```

### Multiline Statements

Multiline statements are classified as a single unit:

```python
result = complexFunction(
    arg1,
    arg2,
    arg3
)  # Entire statement is classified as Assignment
```

### Docstrings

Docstring content is never modified - all internal formatting, blank lines, and special characters are preserved exactly:

```python
def example():
    """
    This docstring content is preserved exactly.

    # This is NOT treated as a comment

    All blank lines inside are preserved.
    """
    pass
```

## Comment Handling

Spacing has special rules for comments:

1. **Consecutive comments** - No blank lines inserted between comment lines
   ```python
   # Copyright header line 1
   # Copyright header line 2
   # Copyright header line 3
   ```

2. **Comment breaks** - Blank line added before a comment (unless previous line was also a comment)
   ```python
   x = 1

   # This comment gets a blank line before it
   y = 2
   ```

3. **After comments** - Existing spacing preserved (leave-as-is policy)
   ```python
   # Comment

   import os  # Existing blank line preserved

   # Comment
   x = 1  # No blank line (preserved)
   ```

## Scope and Blank Lines

Spacing applies rules independent of scope:

```python
def outer():
  x = 1
  y = 0
  z = 0

  print('Level 1')

  def inner():
    y += 1

    print('Level 2')

    if condition:
      z += 1
```

Rules are applied separately for:
- Module level (indent 0)
- Inside `outer()` function (indent 2)
- Inside `inner()` function (indent 4)
- Inside `if` block (indent 6)

## Exit Codes

- **0** - Success: No changes needed or changes applied successfully
- **1** - Failure: Changes needed (in `--check` mode) or processing error occurred

## Integration

### Pre-commit Hook

Add to `.pre-commit-config.yaml`:

```yaml
repos:
  - repo: local
    hooks:
      - id: spacing
        name: spacing
        entry: spacing
        language: system
        types: [python]
```

### CI/CD

```bash
# Check formatting in CI
spacing --check src/
if [ $? -ne 0 ]; then
    echo "Code needs formatting. Run: spacing src/"
    exit 1
fi
```

### Editor Integration

Most editors can be configured to run spacing on save or as a format command.

## Examples

### Before and After

**Before:**
```python
import os
import sys
def main():
    x = 1
    y = 2
    if x > 0:
        print(x)
    else:
        print(y)
    for i in range(10):
        process(i)
    class Helper:
        pass
```

**After (with default config):**
```python
import os
import sys

x = 1
y = 2

if x > 0:
    print(x)
else:
    print(y)

for i in range(10):
    process(i)

class Helper:
    pass
```

## Comparison with Other Tools

| Feature                 | Spacing           | Black                 | Ruff                  |
|-------------------------|-----------------|-----------------------|-----------------------|
| Blank line rules        | ✅ Configurable | ✅ Fixed              | ✅ Fixed              |
| Scope-aware spacing     | ✅ Yes          | ⚠️  Limited            | ⚠️  Limited            |
| Indentation handling    | ✅ Configurable | ⚠️  Enforces/reformats | ⚠️  Enforces/reformats |

**Spacing's Focus**: Spacing solves **one problem exceptionally well** - scope-aware, configurable blank line enforcement. This is a unique capability that Black and Ruff don't provide comprehensively.

**Key Differentiators**:
- **Configurable blank line rules** - Control spacing between any block type transition
- **Independent scope-level processing** - Rules applied within each scope equally
- **Works with your indentation** - Detects existing style, never reformats it

**Philosophy**: Spacing is designed to work **alongside** Black or Ruff, not replace them. Use Black/Ruff for general formatting (line length, quotes, imports) and Spacing for blank line intelligence.

## Troubleshooting

### Files Not Being Modified

1. Check if files already match the rules: `spacing --check file.py`
2. Use verbose mode to see what's happening: `spacing --verbose file.py`
3. Verify your configuration: check `spacing.toml` syntax

### Unexpected Blank Lines

1. Review your configuration file (`spacing.toml`)
2. Use `--dry-run` to preview changes: `spacing --dry-run file.py`
3. Check for comment blocks that may trigger special rules
4. Verify indentation consistency (tabs vs spaces)

### Configuration Not Being Applied

1. Ensure `spacing.toml` is in the current directory or specify with `--config`
2. Check TOML syntax is valid
3. Verify values are in valid range (0-3)
4. Check block type names match documentation

## Contributing

Contributions are welcome! We appreciate bug reports, feature requests, and code contributions.

Please read [CONTRIBUTING.md](CONTRIBUTING.md) for detailed guidelines on:
- Reporting bugs
- Suggesting features
- Development setup
- Coding standards
- Testing requirements
- Submitting merge requests

### Quick Start for Contributors

1. Fork the repository
2. Create a feature branch
3. Add tests for any new functionality
4. Ensure all tests pass: `PYTHONPATH=src pytest test/`
5. Run code quality checks: `ruff check` and `ruff format`
6. Submit a merge request

## Security

For security vulnerabilities, please see [SECURITY.md](SECURITY.md) for our security policy and reporting procedures.

## License

See the LICENSE file for details.

## Acknowledgments

Spacing was inspired by the philosophy of tools like Black and Ruff - that automated formatting allows developers to focus on logic rather than style.
