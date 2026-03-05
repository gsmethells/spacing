# Spacing - Design Document

## Overview

Python code formatter enforcing configurable blank line rules. Processes files in-place, applying scope-aware blank line rules while preserving multiline formatting and docstring content.

## Architecture

### Core Components

1. **MultilineParser** (`parser.py`): Line-by-line reading with bracket/quote tracking for multiline statements
2. **StatementClassifier** (`classifier.py`): Statement type identification with pre-compiled regex patterns
3. **FileAnalyzer** (`analyzer.py`): File structure parsing and analysis
4. **ContextBuilder** (`context.py`): Pre-compute statement relationships in O(n) (new in v1.0.0)
5. **BlankLineRuleEngine** (`rules.py`): Context-based rule application with specialized handlers
6. **CommentRuleHandler** (`commentrules.py`): Comment-specific blank line rules
7. **DefinitionRuleHandler** (`definitionrules.py`): PEP 8/257 definition and docstring rules
8. **Helper Functions** (`helpers.py`): Pure stateless functions for statement analysis
9. **BlankLineConfig** (`config.py`): Singleton configuration system (TOML-based)
10. **PathFilter** (`pathfilter.py`): Smart path discovery with configurable exclusions
11. **CLI Interface** (`cli.py`): Command-line interface with check/dry-run modes
12. **FileProcessor** (`processor.py`): Atomic file I/O with change detection

### Processing Pipeline

**Configuration**: Singleton pattern, TOML parsing with 0-3 validation, path exclusions

**Path Discovery**: Automatic `.py` file discovery with smart exclusions (hidden dirs, venv, build artifacts)

**Two-Pass Processing** (refactored for O(n) performance):
1. **Pass 1 - Analyze + Build Context**:
   - `FileAnalyzer`: MultilineParser + StatementClassifier → Statement list with block types
   - `ContextBuilder`: Pre-compute all relational info (prev/next statements, scope changes, completed blocks) in single O(n) pass
2. **Pass 2 - Apply Rules + Reconstruct**:
   - `BlankLineRuleEngine`: Apply configuration-driven rules using pre-computed context (no backward scanning)
   - Specialized handlers: `CommentRuleHandler`, `DefinitionRuleHandler`
   - `FileProcessor`: Atomic write (tempfile + rename) only if changes detected

**Key Innovation**: `StatementContext` caches all relational data, eliminating O(n²) backward scanning during rule application

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
3. Flow Control (return, yield, yield from)
4. Call (function calls, del, assert, pass, raise)
5. Import
6. Control (if/for/while/try/with structures)
7. Definition (def/class)
8. Declaration (global/nonlocal)
9. Comment

### 7. Scope-Aware Processing
- Rules applied independently at each indentation level
- Secondary clauses (elif/else/except/finally): No blank lines before
- Scope boundaries: Always 0 blank lines at start/end (non-configurable)

### 8. Performance Optimization (v1.1 Refactoring)

**Problem**: Original implementation had O(n²)-O(n³) complexity with deep nesting (6-7 levels) and 692-line monolithic `rules.py`

**Solution**: Context-based architecture with pre-computation:

**StatementContext Pattern**:
- Pre-compute all relational information (prev/next statements, scope changes, completed blocks) in a forward pass
- Cache in `StatementContext` dataclass attached to each statement
- XXX: `_computeScopeInfo` returning-from-nested detection uses O(n²) backward scan; acceptable for typical file sizes
- Eliminates most O(n²) backward scanning during rule application

**Specialized Handlers**:
- `CommentRuleHandler`: Comment-specific rules (guard clauses, max 3-level nesting)
- `DefinitionRuleHandler`: PEP 8/257 rules for definitions and docstrings
- `HelperFunctions`: Pure stateless functions for statement analysis

**Results**:
- Complexity: O(n²)-O(n³) → O(n) for rule application (context build has O(n²) worst case for scope detection)
- Code size: 692 lines → 248 lines (64% reduction)
- Max nesting: 6-7 levels → 3 levels max
- Max parameters: 10 → 4
- Passes: 3+ → exactly 2
- Maintainability: 1 monolithic file → 5 focused modules

### 9. Comment Handling

**Philosophy**: Comments are paragraph markers - preserve user intent for adjacent blank lines

**Rules**:
- Blank lines directly adjacent to comments are preserved
- Transitioning from non-comment to comment: Add blank line (comment break rule)
- Scope boundaries override: Never preserve blank lines at scope start
- Implementation: `preserveExistingBlank` flag + `startsNewScope` precedence check

### 10. Directive System

**`# spacing: skip` Directive**:
- Standalone comment marks following consecutive statements to skip blank line rules
- Directive comment kept in output for idempotency (like Black's `# fmt: skip`)
- Case-insensitive and whitespace-tolerant pattern matching
- Block ends at first blank line or end of file

**Implementation Details**:
- `Statement.skipBlankLineRules` flag added to dataclass
- Detection in `FileAnalyzer._processDirectives()` after initial parsing
- Skip statements preserve existing blank line count
- Statements after skip blocks use `max(existing, calculated)` to respect PEP 8
- `StatementContext.preserveBlankLines` flag marks statements that should preserve their blank lines

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

Comprehensive test suite (316 tests, >95% coverage) covering:
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
