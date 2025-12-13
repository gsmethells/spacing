# Spacing - Design Document

## Overview

Python code formatter enforcing configurable blank line rules. Processes files in-place, applying scope-aware blank line rules while preserving multiline formatting and docstring content.

## Architecture

### Core Components

1. **MultilineParser** (`parser.py`): Line-by-line reading with bracket/quote tracking for multiline statements
2. **StatementClassifier** (`classifier.py`): Statement type identification with pre-compiled regex patterns
3. **BlankLineRuleEngine** (`rules.py`): Configurable blank line rules based on block transitions
4. **FileAnalyzer** (`analyzer.py`): File structure parsing and analysis
5. **BlankLineConfig** (`config.py`): Singleton configuration system (TOML-based)
6. **PathFilter** (`pathfilter.py`): Smart path discovery with configurable exclusions
7. **CLI Interface** (`cli.py`): Command-line interface with check/dry-run modes
8. **FileProcessor** (`processor.py`): Atomic file I/O with change detection

### Processing Pipeline

**Configuration**: Singleton pattern, TOML parsing with 0-3 validation, path exclusions

**Path Discovery**: Automatic `.py` file discovery with smart exclusions (hidden dirs, venv, build artifacts)

**Three-Pass Processing**:
1. **FileAnalyzer**: MultilineParser + StatementClassifier → Statement list with block types
2. **BlankLineRuleEngine**: Apply configuration-driven rules per indentation level
3. **FileProcessor**: Atomic write (tempfile + rename) only if changes detected

## Key Design Decisions

### 1. Singleton Configuration
- Global `config` instance eliminates parameter threading
- `setConfig()` allows CLI updates
- TOML-based customization via `spacing.toml`
- Default: 1 blank line between different block types

### 2. Atomic File Operations
- Write to `.spacing_temp_<random>`, then rename
- Preserves original file on failure
- Maintains EOF newline presence/absence
- UTF-8 encoding with error handling

### 3. Pre-compiled Regex Patterns
- Module-level compilation for performance
- `COMPILED_PATTERNS` and `COMPILED_SECONDARY_CLAUSES` dictionaries
- Eliminates per-statement compilation overhead

### 4. Multiline Statement Handling
- Buffer physical lines until logical statement completes
- Preserve original line breaks within statements
- Classify complete statement (e.g., multiline assignment → Assignment block)
- Track `inString` state with `stringDelimiter` for quote matching

### 5. Docstring Preservation
**Critical: Docstrings are atomic units - internal structure NEVER modified**

- Triple-quoted strings tracked from open to close
- All internal content preserved: blank lines, `#` characters, indentation, formatting
- `parser.inString` checked before processing blank lines/comments

**PEP 257 Compliance**:
- Module/class docstrings: Always 1 blank line after (non-configurable)
- Function/method docstrings: Configurable via `afterDocstring` (default: 1)
- Docstring-to-docstring: Always 0 blank lines

**PEP 8 Compliance**:
- Module-level (indent 0) definitions: 2 blank lines between consecutive def/class
- Nested definitions: 1 blank line (or `consecutiveDefinition` config value)

### 6. Block Classification Priority

Precedence (highest to lowest):
1. Type Annotation (PEP 526 type annotations with or without default values)
2. Assignment (assignments, comprehensions, lambdas)
3. Call (function calls, del, assert, pass, raise, yield, return)
4. Import
5. Control (if/for/while/try/with structures)
6. Definition (def/class)
7. Declaration (global/nonlocal)
8. Comment

### 7. Scope-Aware Processing
- Rules applied independently at each indentation level
- Secondary clauses (elif/else/except/finally): No blank lines before
- Scope boundaries: Always 0 blank lines at start/end (non-configurable)

### 8. Comment Handling

**Philosophy**: Comments are paragraph markers - preserve user intent for adjacent blank lines

**Rules**:
- Blank lines directly adjacent to comments are preserved
- Transitioning from non-comment to comment: Add blank line (comment break rule)
- Scope boundaries override: Never preserve blank lines at scope start
- Implementation: `preserveExistingBlank` flag + `startsNewScope` precedence check

### 9. Directive System

**`# spacing: skip` Directive**:
- Standalone comment marks following consecutive statements to skip blank line rules
- Directive comment kept in output for idempotency (like Black's `# fmt: skip`)
- Case-insensitive and whitespace-tolerant pattern matching
- Block ends at first blank line or end of file

**Implementation Details**:
- `Statement.skipBlankLineRules` flag added to dataclass
- Detection in `FileAnalyzer._processDirectives()` after initial parsing
- Rule engine uses two-track prevBlockType system:
  - `prevBlockType`: Includes skip statements (for PEP 8 when skip at file start)
  - `prevNonSkipBlockType`: Excludes skip statements (for normal rule application)
- Skip statements preserve existing blank line count
- Statements after skip blocks use `preserveExistingBlank` with `max(1, calculated)` to respect PEP 8
- `_convertToBlankLineCounts()` skips over skip-marked statements when finding previous statement

## Configuration

### Structure
```python
@dataclass
class BlankLineConfig:
  defaultBetweenDifferent: int = 1
  transitions: dict  # Fine-grained overrides (e.g., 'assignment_to_call': 2)
  consecutiveControl: int = 1
  consecutiveDefinition: int = 1
  afterDocstring: int = 1
  indentWidth: int = 2
  excludeNames: list  # Path exclusions
  excludePatterns: list  # Glob exclusions
  includeHidden: bool = False
```

### TOML Format
```toml
[blank_lines]
default_between_different = 1
consecutive_control = 1
consecutive_definition = 1
after_docstring = 1
indent_width = 2
# Fine-grained: <from_block>_to_<to_block> = <count>
assignment_to_call = 2

[paths]
exclude_names = ["generated"]
exclude_patterns = ["**/old_*.py"]
include_hidden = false
```

Block type names: `type_annotation` (or `annotation`), `assignment`, `call`, `import`, `control`, `definition`, `declaration`, `docstring`, `comment`

## Error Handling

**Strategy**:
- CLI: Catch and log errors, continue processing other files
- Processor: Return boolean (True = changes made, False = no changes/error)
- Configuration: Raise exceptions for invalid config (fail fast)

**Exceptions**:
- `FileNotFoundError`, `PermissionError`, `UnicodeDecodeError`, `OSError`: Logged, processing continues
- `TOMLDecodeError`: Propagated to user

## Performance Optimizations

1. Pre-compiled regex patterns (module-level)
2. Singleton configuration (load once)
3. Atomic file operations (write temp, rename only if changed)
4. Change detection (line-by-line comparison)
5. Two-pass processing (analyze once, apply rules once)
6. Efficient bracket tracking (character scanning, no AST)

## Testing

Comprehensive test suite (217 tests, >90% coverage) covering:
- Unit tests per component (parser, classifier, rules, analyzer, processor, config)
- Integration tests (end-to-end, configuration-driven, docstrings, class methods, nested scopes)
- Directive tests (16 tests): Detection, idempotency, edge cases, integration
- Bug regression tests
- CLI tests
- Configuration validation tests

See `test/` directory for details.

## Strategic Direction

**Mission**: Definitive solution for scope-aware, configurable blank line enforcement

**Focus**: Become best-in-class at blank line intelligence - a capability Black/Ruff don't comprehensively provide

**Future**:
- Parallel processing for large codebases
- Multi-language support (JavaScript, TypeScript, Java)
- Integration API for Ruff/other formatters
- Structured logging for debugging

**Out of Scope**: Line length, import sorting, quote normalization, general formatting (avoid becoming "yet another formatter")
