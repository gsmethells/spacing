# Local Claude Code Rules for Prism Project

These rules are specific to the prism blank line enforcement project and supplement the main CLAUDE.md rules.

## Bug Fix Process

- For each bug fix, add a very concise one-line entry to the CHANGELOG.md file
- Include the version number and date of the fix
- Keep entries short and focused on the specific issue that was resolved

## Version Management

- Bump the patch version in pyproject.toml for each bug fix release
- Update the CHANGELOG.md with the new version and fixes included
- Use semantic versioning: MAJOR.MINOR.PATCH

## Testing Requirements

- Every bug fix must include a regression test to prevent the issue from reoccurring
- Add new tests to the appropriate test file in the `test/` directory
- Run the full test suite before completing any bug fix

## Code Quality

- All code must pass `ruff check` and `ruff format` before completion
- Follow the existing code patterns and naming conventions
- Maintain comprehensive docstrings for all public methods