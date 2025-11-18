# Rules

**IMPORTANT**: This file contains language-agnostic rules that must be followed concerning coding standards and workflows for all projects.

## Language-Specific Standards

Uncomment the language(s) used in this project:

@python-code-standard.md
`@java-code-standard.md`
`@cpp-code-standard.md`
`@javascript-code-standard.md`

**Note**: These language standard files are committed to version control and shared across the team. For personal overrides, create a `CLAUDE.local.md` file (gitignored) in your local repository.

## General Code Standards

### Headers
- Include a copyright header in files with at least one line of code
  - use the first three lines from the COPYRIGHT file
  - use a language-specific comment style

### Spaces and Wrapping
- Use appropriate indentation for your language (follow language conventions)
- Wrap lines at 120 characters
- Do NOT leave space characters at the end of a line
- Use consistent formatting throughout the codebase

### Control Flow

**MANDATORY**: Always follow these rules regarding control flow.

- Use exceptions instead return statements for control flow between caller/callee when there are errors
- Use only one return statement in a function/method unless:
  - the extra return statement is part of a guard clause near the beginning of the function/method
  - the extra return statement is part of an inner function definition
- Always include an "else" clause when an if-statement has an "else if" clause

### Documentation
- Document complex business logic
- Include XXX comments for non-obvious logic or important implementation notes

## Project Structure
- Keep code modular aiming to maintain a Separation of Concerns
- Keep functions and methods short and focused
- Organize code into logical packages based upon the purpose of the class/module
- Follow existing directory/package structure patterns
- Use environment variables for configuration
- Keep configuration separate from business logic

### Error Handling
- Use custom exception classes for domain-specific errors
- Include meaningful error messages
- Use retry mechanisms for network operations
- Log errors appropriately with context

### Security
- Use secure defaults for all configurations
- Validate all input data
- Follow security best practices

### Performance
- Use appropriate data structures
- Use async/await where appropriate
- Consider memory usage for I/O operations
- Achieve correctness first and optimize later: this prevents premature optimization

### Code Quality & Linting
- Use language-specific linters and formatters as defined in CLAUDE.local.md
- All code must pass linting checks before committing
- Configure linting tools in project root (e.g., .eslintrc, .clang-format, etc.)
- Common issues to avoid across all languages:
  - Unused imports or variables
  - Lines that are too long (follow 120 character limit)
  - Inconsistent formatting
  - Use of deprecated features

### Testing

#### General Standards
- **MANDATORY**: When fixing a bug, **always** add regression tests to the existing unit test suite
- Prefer short, to-the-point tests that test situations corresponding to a single use case
- Do not call private methods directly inside unit tests
- Never mock methods of the class under test
- Use mocks only when necessary, for example:
  - when using a third-party interface (e.g, an API call) **always** use a mock
  - when natural set up would be too difficult (e.g., a race condition)

#### Unit Tests
- Add tests to the appropriate existing test file (e.g., `test/parser/test_featureextractor.py`)
- Include clear documentation in test names and docstrings explaining what bug the test prevents
- Test both success and failure scenarios for the function/method
- Aim for complete test coverage of the function/method
- Do not let unit tests become integration tests: focus on testing the function/method at-hand

## Implementation Consistency

When making any design change or decision that affects multiple parts of the codebase:

1. Trace all implications - Identify every file, function, comment, error message, and documentation that needs updating
2. Update everything consistently - Don't leave stale comments, outdated error messages, or mismatched function signatures
3. Follow the change through the entire call stack - From entry points to helper functions to error handling
4. Verify consistency before presenting - Check that all related code reflects the new design

Examples of consistency failures to avoid:
- Changing what a function does but not updating its documentation
- Updating function parameters but missing some call sites
- Changing error conditions but not updating error messages
- Modifying data structures but leaving old field names in comments

Verification checklist:
- Do all error messages match what's actually being checked?
- Do all function signatures match their calls?
- Do all comments reflect current behavior?
- Are all related files updated consistently?

## Design and Development

**IMPORTANT**: This project uses structured workflows for design and code review:
- Use `/design` command for design discussions and solution proposals (works with plan mode)
- Use `/review` command for comprehensive code reviews
- The Code Implementation Workflow below is **MANDATORY** for all code changes

### Code Implementation Workflow

**MANDATORY**: Always follow this approach when writing any code.

When implementing code changes:
- Follow all coding standards in this file and CLAUDE.local.md at all times
- Maintain a todo list to stay organized
- Maintain a `DESIGN.md` file in the project base directory covering:
  - Overview
  - Architecture
  - Important design decisions
- Set up and use appropriate development environment for your language
- When fixing tests, only run the failing tests during iteration
- Update `DESIGN.md` immediately after making significant code changes
- Run language-specific linters and formatters as specified in CLAUDE.local.md

### Project-Specific Context

When working on this project:
- Act as an expert software engineer with deep knowledge of medical devices and ISO 62304/TIR 45
- Consider regulatory compliance requirements in all design and implementation decisions
- Prioritize safety, traceability, and documentation as required by medical device standards
