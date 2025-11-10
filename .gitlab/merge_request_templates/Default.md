## Description

<!-- Provide a clear description of the changes in this MR -->

## Related Issues

<!-- Link to related issues using: Closes #123, Relates to #456 -->

Closes #
Relates to #

## Type of Change

<!-- Mark the appropriate option with an 'x' -->

- [ ] Bug fix (non-breaking change that fixes an issue)
- [ ] New feature (non-breaking change that adds functionality)
- [ ] Breaking change (fix or feature that would cause existing functionality to not work as expected)
- [ ] Documentation update
- [ ] Performance improvement
- [ ] Code quality improvement (refactoring, cleanup)
- [ ] Test coverage improvement

## Changes Made

<!-- Summarize the key changes made in this MR -->

-
-
-

## Testing

### Test Plan

<!-- Describe how you tested these changes -->

**Manual testing**:
-
-

**Automated tests**:
- [ ] Added new tests for new features
- [ ] Added regression tests for bug fixes
- [ ] All existing tests pass
- [ ] Test coverage maintained or improved

### Test Commands

```bash
# Commands used to verify the changes
PYTHONPATH=src pytest test/ -v
```

## Code Quality Checklist

- [ ] Code follows project coding standards (see CLAUDE.md)
- [ ] Self-reviewed the code
- [ ] Code has been formatted with `ruff format`
- [ ] Code passes `ruff check` with no errors
- [ ] Code has been formatted with `spacing` itself
- [ ] Added/updated docstrings for public functions
- [ ] Comments added for complex logic
- [ ] No unnecessary debug code or print statements

## Documentation

- [ ] Updated README.md (if user-facing changes)
- [ ] Updated design.md (if architectural changes)
- [ ] Updated CHANGELOG.md with entry for this change
- [ ] Updated configuration examples (if config changes)

## Breaking Changes

<!-- If this is a breaking change, describe the impact and migration path -->

**Impact**:

**Migration path**:

## Performance Impact

<!-- Describe any performance implications of these changes -->

- [ ] No performance impact
- [ ] Performance improvement (describe below)
- [ ] Potential performance regression (describe and justify below)

## Screenshots/Examples

<!-- If applicable, add screenshots or example output -->

**Before**:
```python

```

**After**:
```python

```

## Deployment Notes

<!-- Any special considerations for deployment? -->

## Checklist for Reviewers

- [ ] Code is clear and maintainable
- [ ] Tests adequately cover the changes
- [ ] Documentation is accurate and complete
- [ ] No security concerns
- [ ] Performance is acceptable
- [ ] Changes align with project goals

---

**Additional Notes**:

<!-- Any additional information for reviewers -->

/label ~"needs review"
