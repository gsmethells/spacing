# Spacing

[![Pipeline Status](https://gitlab.com/oldmission/spacing/badges/main/pipeline.svg)](https://gitlab.com/oldmission/spacing/-/pipelines)
[![Coverage](https://gitlab.com/oldmission/spacing/badges/main/coverage.svg)](https://gitlab.com/oldmission/spacing/-/graphs/main/charts)
[![PyPI Version](https://img.shields.io/pypi/v/spacing.svg)](https://pypi.org/project/spacing/)
[![Python Versions](https://img.shields.io/pypi/pyversions/spacing.svg)](https://pypi.org/project/spacing/)
[![License: GPL v3](https://img.shields.io/badge/License-GPLv3-blue.svg)](https://www.gnu.org/licenses/gpl-3.0)

A Python code formatter that enforces configurable blank line rules between code blocks.

## Overview

While tools like Black and Ruff excel at formatting code (line length, quotes, imports), they apply fixed, non-configurable rules for blank lines. This leaves a gap: teams often want different blank line styles, and existing tools don't handle scope-aware spacing well.

**Spacing fills this gap.** It provides:
- **Configurable blank line rules** - Define exactly how many blank lines between any block type transition
- **Scope-aware processing** - Rules apply independently at each indentation level (module, function, class, control block)
- **Works with your style** - Detects your existing indentation; never reformats it

**The result:** Consistent, readable blank line formatting that matches your team's preferences, without fighting your existing formatter.

## Why Spacing?

**Problem**: You use Black or Ruff for formatting, but you want:
- Zero blank lines between imports and the first statement
- Two blank lines before all class definitions (not just top-level)
- One blank line between consecutive `if` statements
- Different rules at different scope levels

**Solution**: Black and Ruff don't support this level of configurability. Spacing does.

**Use case**: Run Spacing alongside Black/Ruff. Black handles general formatting, Spacing handles blank lines. They complement each other.

## Features

- **Configurable blank line rules** - Customize spacing between different code block types
- **Smart block detection** - Identifies assignments, calls, imports, control structures, definitions, and comments
- **Multiline statement support** - Properly handles statements spanning multiple lines
- **Docstring preservation** - Never modifies content within docstrings
- **Scope-aware processing** - Applies rules independently at each indentation level
- **Comment-aware** - Preserves intentional spacing around comment blocks
- **Safe file operations** - Atomic writes with automatic rollback on errors
- **Change detection** - Only modifies files that need formatting
- **Preview modes** - Dry-run and check modes for verification

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
# Format all Python files in current directory
spacing

# Format a single file
spacing myfile.py

# Format all Python files in a directory
spacing src/

# Check if files need formatting (exit code 1 if changes needed)
spacing --check

# Preview changes without applying them
spacing --dry-run

# Show detailed output
spacing --verbose

# Show version
spacing --version
```

### Automatic File Discovery

When run without path arguments, `spacing` automatically:
- Discovers all `.py` files in the current directory recursively
- Excludes common directories: hidden folders (`.git`, `.venv`), virtual environments (`venv`, `env`), and build artifacts (`build`, `dist`, `__pycache__`, `*.egg-info`)
- Respects custom exclusions in `spacing.toml`

**Note**: Exclusions only apply during automatic discovery. Explicitly specified paths (e.g., `spacing venv/`) bypass exclusions.

## Configuration

### Default Behavior

Spacing uses these defaults (PEP 8 compliant):
- **1 blank line** between different block types
- **1 blank line** between consecutive control structures (`if`, `for`, `while`, `try`, etc.)
- **2 blank lines** between top-level (module-level) function/class definitions
- **1 blank line** between method definitions inside classes
- **0 blank lines** between statements of the same type (except 1 between consecutive control blocks)

### Configuration File

Create `spacing.toml` in your project root:

```toml
[blank_lines]
# Default spacing between different block types (0-3)
default_between_different = 1

# Spacing between consecutive control blocks
consecutive_control = 1

# Spacing between consecutive definitions
consecutive_definition = 1

# Blank lines after function/method docstrings (0-3)
# Note: Module and class docstrings always get 1 blank line (PEP 257)
after_docstring = 1

# Indent width for scope detection (spaces per indent level)
indent_width = 2

# Fine-grained transition overrides
# Format: <from_block>_to_<to_block> = <count>
assignment_to_call = 2
call_to_assignment = 2
import_to_definition = 0

[paths]
# Additional exclusions for automatic discovery
exclude_names = ["generated", "legacy"]
exclude_patterns = ["**/old_*.py"]

# Include hidden directories (default: false)
include_hidden = false
```

### Block Types

Spacing recognizes these code block types (in precedence order):

1. **`assignment`** - Variable assignments, comprehensions, lambda expressions
   ```python
   x = 42
   items = [i for i in range(10)]
   func = lambda x: x * 2
   ```

2. **`call`** - Function/method calls, `del`, `assert`, `pass`, `raise`, `yield`, `return`
   ```python
   print('hello')
   return result
   ```

3. **`import`** - Import statements
   ```python
   import os
   from pathlib import Path
   ```

4. **`control`** - Control structures with blocks (`if`, `for`, `while`, `try`, `with`)
   ```python
   if condition:
       process()

   for item in items:
       handle(item)
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

7. **`docstring`** - Module, class, and function docstrings
   ```python
   """Module docstring."""

   def func():
       """Function docstring."""
       pass
   ```

8. **`comment`** - Comment lines
   ```python
   # This is a comment
   ```

**Precedence**: When a statement matches multiple types, the first matching type is used:
```python
x = someFunction()  # Assignment takes precedence over Call
```

### Configuration Examples

#### Compact style
```toml
[blank_lines]
default_between_different = 0
consecutive_control = 1
consecutive_definition = 1
```

#### Spacious style
```toml
[blank_lines]
default_between_different = 2
consecutive_control = 2
consecutive_definition = 2
```

#### Custom transitions
```toml
[blank_lines]
default_between_different = 1
import_to_assignment = 0  # No blank line after imports
import_to_definition = 2  # Two blank lines before classes
```

### CLI Overrides

```bash
# Use specific config file
spacing --config custom.toml myfile.py

# Ignore configuration file
spacing --no-config myfile.py

# Override specific rules
spacing --blank-lines-default=2 myfile.py
spacing --blank-lines assignment_to_call=2 myfile.py
```

## Directives

### `# spacing: skip`

Skip blank line rules for a specific block of code:

```python
import sys

# spacing: skip
x = 1
y = 2
z = 3

# Normal rules resume after blank line
a = 4
```

**How it works**:
- Place `# spacing: skip` on its own line immediately before the block you want to preserve
- The directive applies to all consecutive statements (no blank lines between them)
- The block ends at the first blank line
- Existing spacing within the block is preserved exactly as-is
- The directive comment remains in the output for idempotency

**Features**:
- **Case-insensitive**: `# SPACING: SKIP` and `# Spacing: Skip` both work
- **Whitespace-tolerant**: `#  spacing:  skip` works too
- **Scope-aware**: Works at any indentation level (module, class, function)

**Example use cases**:
```python
# Preserve compact initialization
# spacing: skip
x = 1
y = 2
z = 3

# Preserve aligned assignments
# spacing: skip
name    = 'John'
age     = 30
city    = 'NYC'

# Keep related statements together
def configure():
  # spacing: skip
  setupLogging()
  initDatabase()
  loadConfig()

  # Normal spacing resumes here
  processData()
```

## How It Works

### Multiline Statements

Statements spanning multiple lines are treated as a single block:

```python
result = complexFunction(
    arg1,
    arg2,
    arg3
)  # Entire statement is one Assignment block
```

### Docstrings

Docstring content is never modified - all internal formatting and blank lines are preserved:

```python
def example():
    """
    This content is preserved exactly.

    # Not treated as a comment

    All internal blank lines preserved.
    """
    pass
```

### Comment Handling

1. **Consecutive comments** - No blank lines between comment lines
   ```python
   # Copyright line 1
   # Copyright line 2
   ```

2. **Comment breaks** - Blank line added before a comment (unless preceded by another comment)
   ```python
   x = 1

   # Comment gets blank line before it
   y = 2
   ```

### Scope-Aware Processing

Rules apply independently at each indentation level:

```python
# Module level (indent 0): 2 blank lines between definitions
def outer():
    # Function level (indent 2): 1 blank line between different blocks
    x = 1

    if condition:
        # Control block level (indent 4): rules apply here too
        process()
```

## Exit Codes

- **0** - Success (no changes needed or changes applied)
- **1** - Failure (changes needed in `--check` mode, or processing error)

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
spacing --check src/ || {
    echo "Code needs formatting. Run: spacing src/"
    exit 1
}
```

## Examples

### Before
```python
import os
import sys
def main():
    x = 1
    y = 2
    if x > 0:
        print(x)
    for i in range(10):
        process(i)
```

### After (default config)
```python
import os
import sys

x = 1
y = 2

if x > 0:
    print(x)

for i in range(10):
    process(i)
```

## Comparison with Other Tools

### What Spacing Does Differently

| Capability                          | Spacing      | Black        | Ruff         |
|-------------------------------------|--------------|--------------|--------------|
| Configure blank lines by block type | ✓ Yes        | ✗ No         | ✗ No         |
| Scope-aware blank line rules        | ✓ Full       | ◐ Partial    | ◐ Partial    |
| Custom transition rules             | ✓ Yes        | ✗ No         | ✗ No         |
| Works with any indentation style    | ✓ Yes        | ✗ Reformats  | ✗ Reformats  |

### Why Use Spacing with Black or Ruff?

**Black and Ruff** are excellent general-purpose formatters that handle:
- Line length wrapping
- Quote normalization
- Import sorting
- Trailing commas
- Overall code structure

**But they don't offer**:
- Configurable blank line rules (you get what they give you)
- Fine-grained control over spacing between block types
- Different rules at different scope levels

**Spacing specializes in blank line management**, providing the configurability and scope-awareness that Black and Ruff intentionally don't support.

### Recommended Workflow

```bash
# 1. Run Black or Ruff for general formatting
black src/
# or: ruff format src/

# 2. Run Spacing for blank line enforcement
spacing src/
```

**Result**: You get Black/Ruff's battle-tested formatting for everything else, plus exactly the blank line style your team wants.

## Troubleshooting

**Files not being modified?**
- Check if files already comply: `spacing --check file.py`
- Use verbose mode: `spacing --verbose file.py`
- Verify `spacing.toml` syntax

**Unexpected blank lines?**
- Review your `spacing.toml` configuration
- Preview changes: `spacing --dry-run file.py`
- Verify indentation consistency (tabs vs spaces)

**Configuration not working?**
- Ensure `spacing.toml` is in the current directory or use `--config`
- Verify TOML syntax is valid
- Check values are in range (0-3 for blank lines, 1-8 for indent_width)
- Verify block type names match documentation

## Contributing

Contributions are welcome! See [CONTRIBUTING.md](CONTRIBUTING.md) for:
- Bug reporting guidelines
- Feature request process
- Development setup
- Coding standards
- Testing requirements
- Merge request procedures

## Security

For security vulnerabilities, see [SECURITY.md](SECURITY.md).

## License

This project is licensed under the GNU General Public License v3.0 or later. See LICENSE for details.
