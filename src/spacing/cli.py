"""
Command line interface for spacing.
Copyright (c) 2025-2026 Greg Smethells. All rights reserved.
See the accompanying AUTHORS file for a complete list of authors.
This file is subject to the terms and conditions defined in LICENSE.
"""

import argparse
import sys
from pathlib import Path

try:
  from importlib.metadata import PackageNotFoundError, version
except ImportError:
  # Python < 3.8
  from importlib_metadata import PackageNotFoundError, version

from .config import BlankLineConfig, setConfig
from .pathfilter import discoverPythonFiles
from .processor import FileProcessor
from .types import BlockType


def getVersion():
  """Get the version of spacing package"""

  versionStr = 'unknown (development)'

  try:
    versionStr = version('spacing')
  except PackageNotFoundError:
    # Package not installed, try to read from pyproject.toml in development
    try:
      import tomllib

      pyproject_path = Path(__file__).parent.parent.parent / 'pyproject.toml'

      if pyproject_path.exists():
        with open(pyproject_path, 'rb') as f:
          data = tomllib.load(f)
          versionStr = data.get('project', {}).get('version', 'unknown')
    except ImportError:
      print(f'Warning: tomllib not available, using fallback version: {versionStr}', file=sys.stderr)
    except FileNotFoundError:
      print(f'Warning: pyproject.toml not found, using fallback version: {versionStr}', file=sys.stderr)
    except PermissionError:
      print(f'Warning: cannot read pyproject.toml, using fallback version: {versionStr}', file=sys.stderr)
    except Exception as e:
      print(f'Warning: error parsing pyproject.toml ({e}), using fallback version: {versionStr}', file=sys.stderr)

  return versionStr


def _processFile(filepath, args):
  """Process a single file and return (changed, exitCode)
  :param filepath: Path to file to process
  :param args: Command line arguments
  :rtype: tuple[bool, int]
  """

  checkOnly = args.check or args.dry_run
  changeDetails = FileProcessor.processFile(filepath, checkOnly=checkOnly, returnDetails=args.dry_run and args.verbose)
  changed = changeDetails if isinstance(changeDetails, bool) else changeDetails[0]

  if changed:
    if args.check or args.dry_run:
      if not args.quiet:
        print(f'would reformat {filepath}')

        if args.verbose and not isinstance(changeDetails, bool):
          _, details = changeDetails

          if details:
            if isinstance(details, tuple):
              summary, diff = details

              print(f'  Changes: {summary}')

              if args.dry_run:
                print(diff)
            else:
              print(f'  Changes: {details}')

      if args.check:
        return (True, 1)
      else:
        return (True, 0)
    else:
      if not args.quiet:
        print(f'reformatted {filepath}')

      return (True, 0)
  else:
    return (False, 0)


def main():
  """CLI entry point"""

  parser = argparse.ArgumentParser(description='Python blank line formatter enforcing spacing rules')

  # Add version argument
  parser.add_argument('--version', action='version', version=f'spacing {getVersion()}', help='Show version and exit')
  parser.add_argument(
    'paths', nargs='*', help='Files or directories to process (default: current directory with smart exclusions)'
  )
  parser.add_argument(
    '--check', action='store_true', help='Check if files need formatting (exit code 1 if changes needed)'
  )
  parser.add_argument('--dry-run', action='store_true', help='Show what changes would be made without applying them')
  parser.add_argument('--verbose', action='store_true', help='Show detailed output for --check or --dry-run mode')
  parser.add_argument('--quiet', action='store_true', help='Suppress all output except errors')

  # Configuration options
  parser.add_argument('--config', type=Path, help='Path to configuration file (default: ./spacing.toml)')
  parser.add_argument('--no-config', action='store_true', help='Ignore configuration file')
  parser.add_argument(
    '--blank-lines-default', type=int, metavar='N', help='Default blank lines between different block types (0-3)'
  )
  parser.add_argument(
    '--blank-lines',
    action='append',
    metavar='FROM_TO=N',
    help='Override blank lines for specific transition (e.g., assignment_to_call=2)',
  )
  parser.add_argument(
    '--blank-lines-consecutive-control',
    type=int,
    metavar='N',
    help='Blank lines between consecutive control blocks (0-3)',
  )
  parser.add_argument(
    '--blank-lines-consecutive-definition',
    type=int,
    metavar='N',
    help='Blank lines between consecutive definition blocks (0-3)',
  )
  parser.add_argument(
    '--blank-lines-after-docstring',
    type=int,
    metavar='N',
    help='Blank lines after docstrings (0-3, default: 1 for PEP 257 compliance)',
  )

  args = parser.parse_args()

  # Load configuration
  try:
    config = loadConfiguration(args)

    setConfig(config)  # Set as global config for singleton access
  except (ValueError, FileNotFoundError) as e:
    print(f'Configuration error: {e}', file=sys.stderr)
    sys.exit(1)

  exitCode = 0
  processedCount = 0
  changedCount = 0

  # If no paths provided, discover Python files in current directory with exclusions
  if not args.paths:
    pythonFiles = discoverPythonFiles(Path.cwd(), config)

    for pyFile in pythonFiles:
      processedCount += 1
      changed, fileExitCode = _processFile(pyFile, args)

      if changed:
        changedCount += 1
        exitCode = max(exitCode, fileExitCode)
  else:
    # Process explicitly provided paths (no exclusions applied)
    for pathStr in args.paths:
      path = Path(pathStr)

      if path.is_file() and path.suffix == '.py':
        processedCount += 1
        changed, fileExitCode = _processFile(path, args)

        if changed:
          changedCount += 1
          exitCode = max(exitCode, fileExitCode)
      elif path.is_dir():
        for pyFile in path.rglob('*.py'):
          processedCount += 1
          changed, fileExitCode = _processFile(pyFile, args)

          if changed:
            changedCount += 1
            exitCode = max(exitCode, fileExitCode)
      else:
        if path.exists():
          print(f'Skipping {path}: not a Python file or directory', file=sys.stderr)
        else:
          print(f'Error: Path not found: {path}', file=sys.stderr)

          exitCode = 1

  if not args.quiet:
    if args.check and exitCode == 0:
      print('All checks passed!')
    elif args.dry_run and changedCount == 0:
      print(f'All {processedCount} files already formatted correctly.')
    elif not (args.check or args.dry_run):
      print(f'Processed {processedCount} files, reformatted {changedCount}.')
    else:
      # args.dry_run is True and changedCount > 0, or args.check is True and exitCode != 0
      # In these cases, individual file messages were already printed above
      pass

  sys.exit(exitCode)


def loadConfiguration(args):
  """Load configuration from file and CLI overrides
  :param args: Parsed command line arguments
  :rtype: BlankLineConfig
  :raises: ValueError for invalid configuration
  :raises: FileNotFoundError if specified config file not found
  """

  # Start with defaults
  config = BlankLineConfig.fromDefaults()

  # Load from config file unless --no-config is specified
  if not args.no_config:
    configPath = args.config or Path('./spacing.toml')

    if configPath.exists():
      try:
        config = BlankLineConfig.fromToml(configPath)
      except (ValueError, FileNotFoundError):
        if args.config:  # Only error if user explicitly specified config
          raise

        # If default config file has issues, just use defaults
        pass

  # Apply CLI overrides
  if args.blank_lines_default is not None:
    validateBlankLineCount(args.blank_lines_default, '--blank-lines-default')

    config.defaultBetweenDifferent = args.blank_lines_default

  if args.blank_lines_consecutive_control is not None:
    validateBlankLineCount(args.blank_lines_consecutive_control, '--blank-lines-consecutive-control')

    config.consecutiveControl = args.blank_lines_consecutive_control

  if args.blank_lines_consecutive_definition is not None:
    validateBlankLineCount(args.blank_lines_consecutive_definition, '--blank-lines-consecutive-definition')

    config.consecutiveDefinition = args.blank_lines_consecutive_definition

  if args.blank_lines_after_docstring is not None:
    validateBlankLineCount(args.blank_lines_after_docstring, '--blank-lines-after-docstring')

    config.afterDocstring = args.blank_lines_after_docstring

  # Parse --blank-lines overrides
  if args.blank_lines:
    for override in args.blank_lines:
      try:
        transitionKey, valueStr = override.split('=', 1)
        value = int(valueStr)

        validateBlankLineCount(value, f'--blank-lines {override}')

        # Parse transition (e.g., "assignment_to_call")
        parts = transitionKey.split('_to_')

        if len(parts) != 2:
          raise ValueError(f'Invalid transition format in --blank-lines {override}. Expected: blocktype_to_blocktype=N')

        fromBlockName, toBlockName = parts
        fromBlock = parseBlockTypeName(fromBlockName)
        toBlock = parseBlockTypeName(toBlockName)
        config.transitions[(fromBlock, toBlock)] = value
      except ValueError as e:
        if '=' not in override:
          raise ValueError(f'Invalid format for --blank-lines: {override}. Expected: blocktype_to_blocktype=N')
        else:
          raise ValueError(f'Invalid --blank-lines override: {e}')

  return config


def validateBlankLineCount(value: int, option: str):
  """Validate blank line count for CLI options
  :param value: Value to validate
  :type value: int
  :param option: Option name for error messages
  :type option: str
  :raises: ValueError if invalid
  """

  if value < 0 or value > 3:
    raise ValueError(f'{option} must be between 0 and 3, got: {value}')


def parseBlockTypeName(name: str) -> BlockType:
  """Parse block type name for CLI
  :param name: Block type name
  :type name: str
  :rtype: BlockType
  :raises: ValueError if invalid
  """

  blockTypeMap = {
    'assignment': BlockType.ASSIGNMENT,
    'call': BlockType.CALL,
    'import': BlockType.IMPORT,
    'control': BlockType.CONTROL,
    'definition': BlockType.DEFINITION,
    'declaration': BlockType.DECLARATION,
    'docstring': BlockType.DOCSTRING,
    'comment': BlockType.COMMENT,
    'flow_control': BlockType.FLOW_CONTROL,
  }

  if name not in blockTypeMap:
    validNames = ', '.join(blockTypeMap.keys())

    raise ValueError(f'Unknown block type: {name}. Valid types: {validNames}')

  return blockTypeMap[name]


if __name__ == '__main__':
  main()
