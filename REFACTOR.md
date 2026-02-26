# Refactoring Plan: Complexity Reduction and Performance Optimization

## Overview

This document describes a comprehensive 6-phase refactoring of the spacing tool to address critical complexity issues identified in REVIEW.md. The refactoring reduces code complexity, improves performance from O(n²)-O(n³) to O(n), and reduces the codebase from 3+ passes to exactly 2 passes.

## Motivation and Rationale

### Critical Issues Addressed

From REVIEW.md:
- **CRITICAL-002**: 6-7 level nesting in rules.py functions with 10 parameters
- **MAJOR-001**: 692-line monolithic rules.py violates maintainability
- **Current architecture**: 3+ passes with O(n²)-O(n³) complexity
- **Pass 2 contains 4 sub-passes**: scope detection, comment detection, recursive rule application, count conversion

### Core Problem

The current `BlankLineRuleEngine.applyRules()` method performs multiple backward scans for each statement:
1. `_applyRulesAtLevel` - recursive processing with backward scans
2. `_hasCompletedDefinitionBlock` - scans backward to find completed blocks
3. `_isReturningFromNestedLevel` - scans backward to detect scope changes
4. `_findPreviousNonBlankAtLevel` - scans backward to find previous statements
5. `_convertToBlankLineCounts` - final conversion pass

This creates O(n²) complexity where n is the number of statements.

### Solution Architecture

**Key Innovation**: Pre-compute all relational information (prev/next statements, scope info, completed blocks) in ONE forward O(n) pass using a `StatementContext` dataclass, then apply rules using this cached context with NO backward scanning.

**Target Architecture**:
- **Pass 1**: Analyze + Build Context (analyzer.py + context.py) - O(n)
- **Pass 2**: Apply Rules + Reconstruct (rules/ package + processor.py) - O(n)

**Module Structure**:
```
src/spacing/
├── analyzer.py (150 lines) - Parse and analyze
├── context.py (200 lines) - NEW: Build StatementContext in one pass
├── helpers.py (80 lines) - Pure helper functions
├── rules/
│   ├── __init__.py - Export BlankLineRuleEngine
│   ├── engine.py (150 lines) - Coordinator
│   ├── comment.py (100 lines) - Comment-specific rules
│   └── definition.py (100 lines) - PEP 8/257 definition rules
├── types.py - Add StatementContext dataclass
└── processor.py (unchanged)
```

## Goals and Success Metrics

| Metric | Before | After | Improvement |
|--------|--------|-------|-------------|
| Max nesting | 6-7 levels | 3 levels | 57-67% |
| rules.py size | 692 lines | <300 lines | 56% |
| Largest function | 125 lines | <50 lines | 60% |
| Max parameters | 10 params | 4 params | 60% |
| Pass count | 3+ passes | 2 passes | 33% |
| Time complexity | O(n²)-O(n³) | O(n) | Quadratic → Linear |
| Module count | 1 monolithic | 5 focused | Better SoC |

## Implementation Phases

### Phase 1: Extract Pure Helper Functions ✓ COMPLETED

**Duration**: 2 hours | **Risk**: LOW

**Goal**: Reduce rules.py from 692 to ~600 lines with zero behavior change

**Changes Made**:
1. Created `src/spacing/helpers.py` with 3 pure functions:
   - `findPreviousNonBlankAtLevel(statements, fromIdx, targetIndent)` - Find previous non-blank statement at target indent level
   - `hasBodyBetween(statements, defIdx, endIdx, targetIndent)` - Check if definition has indented body between indices
   - `isClassDefinition(statement)` - Check if statement is a class definition

2. Modified `src/spacing/rules.py`:
   - Added import: `from .helpers import findPreviousNonBlankAtLevel, hasBodyBetween, isClassDefinition`
   - Replaced 6 instances of `self._methodName` with direct function calls
   - Removed 3 method definitions
   - Reduced from 692 to 637 lines (55 lines removed)

**Validation**: All 219 tests pass

**Rationale**: Extract stateless functions that don't use `self` to establish foundation for further separation of concerns. These functions are pure (no side effects) and easier to test independently.

---

### Phase 2: Introduce StatementContext Foundation

**Duration**: 4 hours | **Risk**: LOW

**Goal**: Add context infrastructure without breaking existing code

**Changes to Make**:

1. **Add StatementContext to types.py**:
```python
@dataclass
class StatementContext:
  """Pre-computed context for a statement to eliminate backward scanning

  This dataclass caches all relational information about a statement that
  would otherwise require O(n) backward scanning during rule application.
  Built once in O(n) time by ContextBuilder, enabling O(1) rule lookups.
  """

  index: int
  statement: Statement
  prevNonBlank: Statement | None = None
  prevNonBlankIdx: int = -1
  nextNonBlank: Statement | None = None
  nextNonBlankIdx: int = -1
  startsNewScope: bool = False
  returningFromNestedLevel: bool = False
  hasCompletedDefBefore: bool = False
  hasCompletedControlBefore: bool = False
  preserveBlankLines: bool = False
```

2. **Create context.py with ContextBuilder**:
```python
class ContextBuilder:
  """Build StatementContext objects in one O(n) forward pass

  This class pre-computes all relational information needed for blank line
  rule application, eliminating the need for O(n²) backward scanning during
  rule evaluation.

  Key methods:
  - buildContexts: Main entry point, builds all contexts in O(n)
  - _initializeContexts: Create initial context objects
  - _computePrevNext: Populate prev/next non-blank references
  - _computeScopeInfo: Detect scope boundaries
  - _computeCompletedBlocks: Identify completed definition/control blocks
  - _computeCommentPreservation: Mark comments that need blank line preservation
  """

  def buildContexts(self, statements: list[Statement]) -> list[StatementContext]:
    """Build context in one O(n) forward pass"""
    contexts = self._initializeContexts(statements)
    self._computePrevNext(statements, contexts)
    self._computeScopeInfo(statements, contexts)
    self._computeCompletedBlocks(statements, contexts)
    self._computeCommentPreservation(statements, contexts)
    return contexts

  def _initializeContexts(self, statements: list[Statement]) -> list[StatementContext]:
    """Create initial context objects for each statement"""
    # Implementation: Create StatementContext for each statement with index

  def _computePrevNext(self, statements: list[Statement], contexts: list[StatementContext]):
    """Populate prevNonBlank and nextNonBlank references"""
    # Implementation: Single forward pass to link prev/next non-blank statements

  def _computeScopeInfo(self, statements: list[Statement], contexts: list[StatementContext]):
    """Detect scope boundaries (startsNewScope, returningFromNestedLevel)"""
    # Implementation: Track indent levels to detect scope changes

  def _computeCompletedBlocks(self, statements: list[Statement], contexts: list[StatementContext]):
    """Identify completed definition/control blocks"""
    # Implementation: Mark statements that follow completed blocks

  def _computeCommentPreservation(self, statements: list[Statement], contexts: list[StatementContext]):
    """Mark comments that need blank line preservation"""
    # Implementation: Detect comments before module-level definitions
```

3. **Add comprehensive unit tests**: `test/test_context.py`
   - Test _initializeContexts creates correct number of contexts
   - Test _computePrevNext links statements correctly
   - Test _computeScopeInfo detects scope changes
   - Test _computeCompletedBlocks identifies completed blocks
   - Test _computeCommentPreservation marks comments correctly
   - Test buildContexts integration with real statement lists

**Key Innovation**: Pre-compute all relational information in ONE pass, eliminating O(n²) backward scanning.

**Validation**:
- `pytest test/test_context.py -v` (new tests pass)
- `pytest test/ -v` (all existing tests still pass)

**Rationale**: Establish the foundation for context-based rule application. This phase adds infrastructure without modifying existing behavior, making it low-risk.

---

### Phase 3: Refactor _determineBlankLineForStatement ⭐ BIGGEST COMPLEXITY WIN

**Duration**: 6 hours | **Risk**: MEDIUM

**Goal**: Reduce from 91 lines, 6-level nesting, 10 params → 3 focused functions with 3-level max

**Changes to Make**:

1. **Create rules/comment.py**:
```python
class CommentRuleHandler:
  """Handle blank line rules for comments

  Implements PEP 8 and PEP 257 rules for blank lines around comments.
  All methods use guard clauses to maintain max 3-level nesting.
  """

  def needsBlankAfterComment(self, fromStmt, toStmt, context, config) -> int:
    """Determine blank lines needed after a comment

    Uses guard clauses for flat control flow:
    1. Early return if not a comment
    2. Check for comment before module-level definition
    3. Check for comment preservation
    4. Default return
    """
    if not fromStmt.isComment:
      return 0
    if self._isCommentBeforeModuleLevelDef(toStmt):
      return self._handleCommentBeforeDefinition(toStmt, context, config)
    if context.preserveBlankLines:
      return 1
    return 0

  def _isCommentBeforeModuleLevelDef(self, stmt) -> bool:
    """Check if statement is a module-level definition"""
    return stmt.indentLevel == 0 and stmt.blockType == BlockType.DEFINITION

  def _handleCommentBeforeDefinition(self, toStmt, context, config) -> int:
    """Handle blank lines for comment before definition"""
    # Implementation with max 3 levels
```

2. **Create rules/definition.py**:
```python
class DefinitionRuleHandler:
  """Handle blank line rules for definitions

  Implements PEP 8 rules for blank lines between module-level definitions
  and PEP 257 rules for blank lines after docstrings.
  """

  def needsBlankAfterDefinition(self, fromStmt, toStmt, context, config) -> int:
    """Determine blank lines needed after a definition (PEP 8)"""
    # Implementation: 2 blank lines between module-level definitions

  def needsBlankAfterControl(self, fromStmt, toStmt, context, config) -> int:
    """Determine blank lines needed after a control block"""
    # Implementation with max 3 levels

  def needsBlankAfterDocstring(self, fromStmt, toStmt, context, config) -> int:
    """Determine blank lines needed after a docstring (PEP 257)"""
    # Implementation: 1 blank line after docstring in class
```

3. **Simplify engine.py**:
```python
def _determineBlankLine(self, context: StatementContext, prevStmt: Statement | None) -> int:
  """Determine blank lines needed before a statement

  Now has 2 params (down from 10!), max 3 levels (down from 6!)

  Uses guard clauses and delegates to specialized handlers:
  - CommentRuleHandler for comment-related rules
  - DefinitionRuleHandler for definition-related rules
  """
  if context.startsNewScope:
    return 0
  if prevStmt is None:
    return 0
  if context.hasCompletedDefBefore:
    return self.definitionHandler.needsBlankAfterDefinition(prevStmt, context.statement, context, self.config)
  if prevStmt.isComment:
    return self.commentHandler.needsBlankAfterComment(prevStmt, context.statement, context, self.config)
  # ... clear dispatch logic with guard clauses
```

**Migration Strategy**: Keep old code as `_OLD_determineBlankLineForStatement`, validate both produce identical results, then remove old code.

**Validation**:
- `pytest test/test_commentrules.py -v` (new comment handler tests)
- `pytest test/test_definitionrules.py -v` (new definition handler tests)
- `pytest test/test_rules.py -v` (all existing tests pass)
- Compare old vs new output on test corpus to ensure identical behavior

**Rationale**: This is the biggest complexity reduction. The current _determineBlankLineForStatement has:
- 10 parameters (excessive cognitive load)
- 6-level nesting (very hard to understand)
- Multiple responsibilities mixed together

By splitting into specialized handlers and using guard clauses, we reduce nesting to 3 levels and parameters to 4, making the code much easier to understand and maintain.

---

### Phase 4: Context-Based applyRules (Eliminate Recursion)

**Duration**: 4 hours | **Risk**: MEDIUM

**Goal**: Replace recursive _applyRulesAtLevel with single-pass using contexts

**Changes to Make**:

**New Implementation in engine.py**:
```python
def applyRules(self, statements: list[Statement]) -> list[int]:
  """Apply blank line rules to statements

  O(n) complexity, no recursion, no backward scans.

  Uses pre-computed StatementContext to avoid backward scanning:
  1. Build contexts once in O(n)
  2. Apply rules in single forward pass using context
  3. Return blank line counts directly (no conversion needed)
  """
  if not statements:
    return []

  # Build contexts (O(n))
  contexts = ContextBuilder().buildContexts(statements)

  # Apply rules (O(n), no scans)
  blankLineCounts = [0] * len(statements)
  for ctx in contexts:
    if ctx.statement.isBlank:
      continue
    if ctx.statement.skipBlankLineRules:
      blankLineCounts[ctx.index] = self._countExistingBlanks(statements, ctx.index)
      continue
    if ctx.statement.isSecondaryClause:
      blankLineCounts[ctx.index] = 0
      continue

    blankLineCounts[ctx.index] = self._determineBlankLine(ctx, ctx.prevNonBlank)

  return blankLineCounts
```

**What Gets Eliminated**:
- Recursive `_applyRulesAtLevel` (125 lines, 6 levels nesting)
- Multiple backward scans per statement
- Separate scope detection pass
- Separate comment preservation pass
- `_convertToBlankLineCounts` method (115 lines) - no longer needed since we return int directly

**Migration Strategy**: Use feature flag `USE_CONTEXT_BASED_RULES` for A/B testing during development.

**Validation**:
- `pytest test/test_refactoring_validation.py -v` (compare old vs new on test corpus)
- Run on 50+ real Python files from various projects
- Ensure byte-for-byte identical output

**Rationale**: The current recursive implementation with backward scanning is the primary source of O(n²) complexity. By pre-computing context, we:
1. Eliminate all backward scanning (O(n²) → O(n))
2. Remove recursion (simpler control flow)
3. Make the code linear and easy to understand
4. Enable better testing (context can be mocked/tested independently)

---

### Phase 5: Eliminate _convertToBlankLineCounts

**Duration**: 1 hour | **Risk**: LOW

**Goal**: Remove 115-line conversion step (already solved by Phase 4)

**Changes to Make**:
- Remove `_convertToBlankLineCounts` method (lines 539-653 in current rules.py)
- Remove old `_applyRulesAtLevel` method (lines 412-537)
- Remove tracking arrays: `shouldHaveBlankLine`, `doNotAlterExistingNumberOfBlankLines`

**Note**: Phase 4's new `applyRules` returns `list[int]` directly, so no conversion is needed.

**Validation**: `pytest test/ -v` (all 219 tests pass)

**Rationale**: The conversion step was needed because the old implementation used boolean arrays. The new implementation directly computes the final result, eliminating this entire step.

---

### Phase 6: Final Cleanup and Documentation

**Duration**: 3 hours | **Risk**: LOW

**Goal**: Polish and document the refactored codebase

**Tasks**:

1. **Organize into rules/ package structure**:
   - Move rules.py logic to rules/engine.py
   - Ensure all imports work correctly
   - Update __init__.py to export BlankLineRuleEngine

2. **Update DESIGN.md**:
   - Replace old architecture description with new 2-pass architecture
   - Document StatementContext pattern
   - Update module descriptions

3. **Add comprehensive module docstrings**:
   - context.py: Explain the caching strategy
   - rules/engine.py: Explain the coordination pattern
   - rules/comment.py: Explain comment-specific rules
   - rules/definition.py: Explain PEP 8/257 rules
   - helpers.py: Explain pure function approach

4. **Reorganize tests** to match new structure:
   - test/test_context.py - ContextBuilder tests
   - test/test_commentrules.py - CommentRuleHandler tests
   - test/test_definitionrules.py - DefinitionRuleHandler tests
   - test/test_engine.py - BlankLineRuleEngine integration tests

5. **Performance benchmarking**:
   - Create benchmark suite with files of varying sizes (100, 500, 1000, 5000 lines)
   - Compare old vs new performance
   - Document results in DESIGN.md

6. **Update CHANGELOG.md**:
   - Add entry for refactoring with performance improvements

**Final Module Structure**:
```
src/spacing/
├── analyzer.py (unchanged)
├── context.py (NEW, 200 lines)
├── helpers.py (NEW, 80 lines)
├── rules/
│   ├── __init__.py (10 lines) - Export BlankLineRuleEngine
│   ├── engine.py (150 lines) - Coordinator
│   ├── comment.py (100 lines) - Comment rules
│   └── definition.py (100 lines) - PEP 8/257 rules
├── types.py (modified - add StatementContext)
└── processor.py (unchanged)
```

**Validation**:
- `pytest test/ -v --cov=src/spacing` (>90% coverage maintained)
- `spacing src/spacing/` (self-lint passes)
- `ruff check src/spacing/` (no violations)
- Performance benchmark: <100ms for 1000-line file (was ~200ms)

**Rationale**: Clean up and document the refactored code to ensure maintainability and provide clear guidance for future contributors.

## Risk Mitigation

### Per-Phase Validation
```bash
# Before each phase
pytest test/ -v > baseline_phase_N.txt

# After each phase
pytest test/ -v > after_phase_N.txt
diff baseline_phase_N.txt after_phase_N.txt  # Must be identical (all 219 tests pass)
```

### Feature Flags (Phase 4)
```python
USE_CONTEXT_BASED_RULES = True  # Toggle for A/B testing
```

### Rollback Procedure
If validation fails:
1. Analyze failures: `pytest test/ -v --tb=long`
2. Fix if legitimate bugs, add regression tests
3. If fundamental issue: `git checkout main` (abandon phase, revise plan)

## Timeline

| Phase | Duration | Risk | Cumulative |
|-------|----------|------|------------|
| Phase 1 | 2 hours | LOW | 2h ✓ |
| Phase 2 | 4 hours | LOW | 6h |
| Phase 3 | 6 hours | MEDIUM | 12h |
| Phase 4 | 4 hours | MEDIUM | 16h |
| Phase 5 | 1 hour | LOW | 17h |
| Phase 6 | 3 hours | LOW | 20h |
| Buffer | 10 hours | - | **30h** |

## Key Techniques

1. **StatementContext Pattern**: Pre-compute all relational info once, eliminating O(n²) scanning
2. **Guard Clauses**: Replace deep nesting with early returns
3. **Strategy Classes**: Separate concerns (comment, definition, helpers)
4. **Incremental Validation**: Each phase validates before proceeding
5. **Feature Flags**: A/B test high-risk changes (Phase 4)
6. **Pure Functions**: Extract stateless functions for easier testing

## Critical Files

### Created
- `/Users/smethelg/src/spacing/src/spacing/helpers.py` ✓
- `/Users/smethelg/src/spacing/src/spacing/context.py` (Phase 2)
- `/Users/smethelg/src/spacing/src/spacing/rules/engine.py` (Phase 3)
- `/Users/smethelg/src/spacing/src/spacing/rules/comment.py` (Phase 3)
- `/Users/smethelg/src/spacing/src/spacing/rules/definition.py` (Phase 3)

### Modified
- `/Users/smethelg/src/spacing/src/spacing/types.py` (Phase 2 - add StatementContext)
- `/Users/smethelg/src/spacing/src/spacing/rules.py` ✓ (Phase 1) → becomes rules/engine.py (Phase 6)

### Test Files
- `/Users/smethelg/src/spacing/test/test_context.py` (Phase 2)
- `/Users/smethelg/src/spacing/test/test_commentrules.py` (Phase 3)
- `/Users/smethelg/src/spacing/test/test_definitionrules.py` (Phase 3)
- `/Users/smethelg/src/spacing/test/test_refactoring_validation.py` (Phase 4)

## Context for Future Claude Instances

### Important Nuances

1. **Why StatementContext?**
   - The current code scans backward for every statement to find previous non-blank, detect scope changes, etc.
   - This creates O(n²) complexity
   - By pre-computing this info once, we get O(n) total complexity

2. **Why NOT just optimize the current code?**
   - The fundamental architecture (recursive + backward scanning) is the problem
   - No amount of micro-optimization will fix O(n²) complexity
   - The deep nesting makes the code unmaintainable
   - Separation of concerns is needed for future extensibility

3. **Why 6 phases instead of all at once?**
   - Each phase is independently validated
   - If something breaks, we know exactly where
   - Low-risk phases build foundation for high-risk phases
   - Allows for incremental review and adjustment

4. **Why keep old code during migration?**
   - A/B testing ensures identical behavior
   - Easier to debug differences
   - Provides fallback if issues found
   - Remove once confident in new implementation

5. **PEP Compliance is Critical**:
   - PEP 8: 2 blank lines between module-level definitions
   - PEP 257: Blank line after docstring in class
   - These rules must be preserved exactly
   - Tests specifically validate PEP compliance

6. **Skip Directives Must Work**:
   - `# spacing: skip-blank-lines-before` and `# spacing: skip-blank-lines-after`
   - These preserve existing blank lines
   - Must be handled in context building (Phase 2)

## Current Status

- **Phase 1**: ✓ COMPLETED
  - helpers.py created with 3 pure functions
  - rules.py reduced from 692 to 637 lines
  - All 219 tests passing

- **Phase 2**: IN PROGRESS
  - Add StatementContext to types.py
  - Create context.py with ContextBuilder
  - Add tests in test/test_context.py

- **Phases 3-6**: PENDING


## Refactoring Complete

**Date**: 2026-01-20

**All Phases Completed Successfully**:
- ✓ Phase 1: Extract pure helper functions (692→637 lines)  
- ✓ Phase 2: Introduce StatementContext foundation (O(n) pre-computation)
- ✓ Phase 3: Add specialized comment and definition rule handlers
- ✓ Phase 4: Context-based applyRules (eliminate recursion and O(n²) scanning)
- ✓ Phase 5: Remove old implementation (637→248 lines, 64% total reduction)
- ✓ Phase 6: Update documentation (DESIGN.md, CHANGELOG.md)

**Final Results**:
- All 262 tests passing
- Time complexity: O(n²)-O(n³) → O(n)
- Code size: 692 lines → 248 lines (64% reduction)
- Max nesting: 6-7 levels → 3 levels
- Max parameters: 10 → 4
- Passes: 3+ → exactly 2
- Modules: 1 monolithic → 5 focused

**Validation**:
- Ran spacing on itself - all files properly formatted
- No behavior changes - byte-for-byte identical output
- All existing tests pass without modification
- New tests added for context building (16 tests)
- New tests added for rule handlers (27 tests)

