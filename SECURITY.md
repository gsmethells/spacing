# Security Policy

## Supported Versions

We actively support the latest major version of Spacing with security updates.

| Version | Supported          |
| ------- | ------------------ |
| 0.7.x   | :white_check_mark: |
| 0.6.x   | :white_check_mark: |
| < 0.6   | :x:                |

## Reporting a Vulnerability

**Please do not report security vulnerabilities through public GitLab issues.**

Instead, please report security vulnerabilities by emailing the maintainers directly. You can find contact information in the AUTHORS file.

### What to Include

When reporting a vulnerability, please include:

1. **Description** of the vulnerability
2. **Steps to reproduce** the issue
3. **Potential impact** of the vulnerability
4. **Suggested fix** (if you have one)
5. **Your contact information** for follow-up questions

### What to Expect

- **Acknowledgment**: We will acknowledge receipt of your report within 48 hours
- **Updates**: We will provide regular updates on our progress
- **Timeline**: We aim to release a fix within 30 days for critical vulnerabilities
- **Credit**: If you wish, we will credit you in the security advisory and release notes

### Security Considerations for Spacing

Spacing is a code formatting tool that:
- **Reads and writes Python files** on your filesystem
- **Does not execute** the code it formats
- **Does not make network requests** (except when installing from PyPI)
- **Has no external runtime dependencies**

Potential security concerns:
1. **File system access**: Spacing needs read/write access to format files
2. **Path traversal**: Ensure you trust the directories you point spacing at
3. **Configuration files**: TOML configuration is parsed; malformed files could cause issues
4. **Supply chain**: Verify package integrity when installing from PyPI

### Best Practices for Users

1. **Verify package integrity**: Check GPG signatures when available
2. **Use virtual environments**: Install spacing in isolated environments
3. **Review changes**: Use `--dry-run` or `--check` before applying changes
4. **Backup your code**: Always use version control before running formatters
5. **Limit permissions**: Don't run spacing with elevated privileges
6. **Trust your sources**: Only run spacing on code you trust

### Security Features

Spacing includes several security-conscious design decisions:

1. **Atomic file operations**: Changes are written to temporary files first, then renamed
2. **No code execution**: Spacing only parses syntax, never executes Python code
3. **Explicit path handling**: No hidden file modifications outside specified paths
4. **Configuration validation**: Input validation on all configuration values
5. **Error handling**: Graceful failure on malformed input

## Disclosure Policy

When a security vulnerability is fixed:

1. We will publish a security advisory on GitLab
2. We will release a patched version on PyPI
3. We will update the CHANGELOG with security-related changes
4. We will credit the reporter (unless they prefer anonymity)

## Security Updates

To stay informed about security updates:

- Watch the [GitLab repository](https://gitlab.com/oldmission/spacing)
- Monitor the [CHANGELOG](CHANGELOG.md) for security-related entries
- Follow releases on [PyPI](https://pypi.org/project/spacing/)

## Vulnerability History

No security vulnerabilities have been reported as of version 0.7.0.

## Questions?

If you have questions about this security policy, please open an issue on GitLab or contact the maintainers directly.
