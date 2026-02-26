# Test Coverage Verification Plan for Refactored Spacing Tool

## Summary

Ensure the major 6-phase refactoring (O(n²)→O(n), 692→248 lines, 64% reduction) has sufficient test coverage for a safe release. Current state: 262 tests, 91.45% coverage.

## Identified Gaps

### 1. Missing Test File
- **`test_helpers.py`** - The new `helpers.py` module (3 pure functions) has no dedicated tests
  - `findPreviousNonBlankAtLevel()` - covered indirectly
  - `hasBodyBetween()` - covered indirectly
  - `isClassDefinition()` - line 70 uncovered

### 2. Coverage Gaps by Module
| Module | Coverage | Missing Lines |
|--------|----------|---------------|
| `helpers.py` | 92.68% | Line 70 (early return), branch 73→78 |
| `commentrules.py` | 91.25% | Lines 143, 168 |
| `definitionrules.py` | 95.65% | Line 104 |
| `rules.py` | 91.33% | Lines 170, 174, 205-209 |
| `cli.py` | 78.63% | Lines 15-17, 32-50, etc. |
| `analyzer.py` | 87.23% | Lines 60, 66-70, 91-100 |

### 3. CI/CD Gap
- No "quick unit test" phase that runs before the full multi-Python-version matrix
- User explicitly requested adding this

### 4. Behavioral Regression Testing
- No tests that verify byte-for-byte identical output vs pre-refactor
- The REFACTOR.md states "no behavior changes" but this is not tested

## Implementation Plan

### Phase 1: Add `test_helpers.py` (NEW)
Create dedicated unit tests for the 3 pure helper functions.

**File:** `test/test_helpers.py`

**Tests to add:**
1. `test_findPreviousNonBlankAtLevelBasic` - find previous statement at same level
2. `test_findPreviousNonBlankAtLevelSkipsBlanks` - skips blank lines
3. `test_findPreviousNonBlankAtLevelNotFound` - returns (None, None) when not found
4. `test_findPreviousNonBlankAtLevelDifferentIndent` - stops at different indent
5. `test_hasBodyBetweenTrue` - definition with body
6. `test_hasBodyBetweenFalse` - definition without body
7. `test_hasBodyBetweenEmptyRange` - no statements between
8. `test_isClassDefinitionTrue` - class definition
9. `test_isClassDefinitionFalseFunction` - function definition (not class)
10. `test_isClassDefinitionFalseNotDefinition` - non-definition block type
11. `test_isClassDefinitionEmptyLines` - statement with no lines

### Phase 2: Add Behavioral Regression Tests (NEW)
Create golden file tests that verify output matches expected formatting.

**File:** `test/test_regression.py`

**Tests to add:**
1. `test_formatSimpleFile` - basic statements (assignment, call, import)
2. `test_formatClassWithMethods` - class definitions with methods
3. `test_formatNestedScopes` - deeply nested control structures
4. `test_formatModuleLevelDefinitions` - PEP 8 two blank lines
5. `test_formatDocstrings` - module, class, function docstrings
6. `test_formatCommentsPreservation` - comment blank line preservation
7. `test_formatSkipDirective` - `# spacing: skip` directive
8. `test_formatDecoratedDefinitions` - decorators with definitions
9. `test_formatSecondaryClause` - elif/else/except handling
10. `test_formatConsecutiveControl` - consecutive if/for/while blocks

**Golden file directory:** `test/golden/`

### Phase 3: Improve Coverage on Existing Modules
Add targeted tests to cover uncovered lines.

**File:** `test/test_commentrules.py` additions:
- Test for line 143: `_hasBlankAfterComment` with no next statement
- Test for line 168: edge case in `_hasCompletedDefinitionBeforeComment`

**File:** `test/test_definitionrules.py` additions:
- Test for line 104: `isModuleLevelDocstring` edge case

**File:** `test/test_rules.py` additions:
- Test for lines 170, 174: `_getExistingBlanks` edge cases
- Test for lines 205-209: `_handleSkipDirective` edge cases

### Phase 4: Add Unit Test Phase to CI
Add a fast "unit test" stage that runs before the full matrix.

**File:** `.gitlab-ci.yml`

**Changes:**
```yaml
# Add new stage
stages:
  - lint
  - unit-test   # NEW - fast feedback
  - test
  - coverage
  - tag
  - publish

# Add quick unit test job
unit-test:quick:
  stage: unit-test
  image: python:3.11
  script:
    - pip install -e .
    - pip install pytest pytest-cov
    - pytest test/ -v --tb=short -x  # Stop on first failure
  rules:
    - if: '$CI_PIPELINE_SOURCE == "merge_request_event"'
    - if: '$CI_COMMIT_BRANCH == $CI_DEFAULT_BRANCH'
    - if: '$CI_COMMIT_TAG'
```

## Files to Create/Modify

### New Files
1. `test/test_helpers.py` - Unit tests for helpers module (~80 lines)
2. `test/test_regression.py` - Behavioral regression tests (~150 lines)
3. `test/golden/*.py` - Golden test input/expected files (~10 files)

### Modified Files
1. `.gitlab-ci.yml` - Add unit-test stage
2. `test/test_commentrules.py` - Add 2-3 edge case tests
3. `test/test_definitionrules.py` - Add 1 edge case test
4. `test/test_rules.py` - Add 2-3 edge case tests

## Verification Steps

After implementation:

1. **Run all tests:**
   ```bash
   pytest test/ -v
   ```
   Expected: All tests pass (262 + ~25 new = ~287 tests)

2. **Check coverage:**
   ```bash
   pytest test/ --cov=src/spacing --cov-report=term-missing
   ```
   Expected: Coverage ≥93%

3. **Self-format check:**
   ```bash
   spacing --check src/ test/
   ```
   Expected: Exit code 0

4. **Lint check:**
   ```bash
   ruff check src/spacing/ test/
   ruff format --check src/spacing/ test/
   ```
   Expected: No violations

5. **CI validation:**
   Push to branch and verify pipeline passes with new unit-test stage

## Risk Assessment

- **Low risk**: All changes are test additions, no production code modified
- **Rollback**: Simple - revert test file additions
- **Impact**: Increases confidence in release safety

## Estimated Work

| Phase | New Tests | Estimated Lines |
|-------|-----------|-----------------|
| Phase 1 | 11 tests | ~80 lines |
| Phase 2 | 10 tests | ~150 lines |
| Phase 3 | ~6 tests | ~40 lines |
| Phase 4 | CI change | ~15 lines |
| **Total** | **~27 tests** | **~285 lines** |