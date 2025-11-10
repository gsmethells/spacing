"""
Path discovery and filtering for spacing.
Copyright (c) 2025-2026 Greg Smethells. All rights reserved.
See the accompanying AUTHORS file for a complete list of authors.
This file is subject to the terms and conditions defined in LICENSE.
"""

from pathlib import Path

# Default exclusions applied during automatic path discovery
DEFAULT_EXCLUDE_NAMES = [
  'venv',
  'env',
  'virtualenv',
  'build',
  'dist',
  '__pycache__',
]

# Glob patterns for default exclusions
DEFAULT_EXCLUDE_PATTERNS = [
  '*.egg-info',
  '*.egg',
]


def shouldExcludePath(path, config, useDefaults=True):
  """Check if a path should be excluded based on configuration
  :param path: Path to check
  :type path: Path
  :param config: Configuration containing exclusion rules
  :type config: BlankLineConfig
  :param useDefaults: Whether to apply default exclusions
  :type useDefaults: bool
  :rtype: bool
  """

  # Convert to Path if string
  if not isinstance(path, Path):
    path = Path(path)

  # Check if path is hidden (starts with .)
  if not config.includeHidden:
    for part in path.parts:
      if part.startswith('.'):
        return True

  # Combine default and user exclusions
  excludeNames = list(DEFAULT_EXCLUDE_NAMES) if useDefaults else []
  excludePatterns = list(DEFAULT_EXCLUDE_PATTERNS) if useDefaults else []

  excludeNames.extend(config.excludeNames)
  excludePatterns.extend(config.excludePatterns)

  # Check exclude_names (simple name matching)
  for part in path.parts:
    if part in excludeNames:
      return True

  # Check exclude_patterns (glob matching)
  for pattern in excludePatterns:
    # Check if the pattern matches the full path
    if path.match(pattern):
      return True

    # Also check if any parent directory matches (for patterns like *.egg-info)
    # This handles cases like foo.egg-info/PKG-INFO
    for parent in path.parents:
      if parent != Path('.') and parent.match(pattern):
        return True

  return False


def discoverPythonFiles(rootPath, config):
  """Discover Python files in directory, applying exclusions
  :param rootPath: Root directory to search
  :type rootPath: Path
  :param config: Configuration containing exclusion rules
  :type config: BlankLineConfig
  :rtype: list[Path]
  """

  # Convert to Path if string
  if not isinstance(rootPath, Path):
    rootPath = Path(rootPath)

  if not rootPath.is_dir():
    return []

  pythonFiles = []

  for pyFile in rootPath.rglob('*.py'):
    # Check if file or any parent directory should be excluded
    if shouldExcludePath(pyFile.relative_to(rootPath), config):
      continue

    pythonFiles.append(pyFile)

  return sorted(pythonFiles)
