"""
File processor with change detection.
Copyright (c) 2025-2026 Greg Smethells. All rights reserved.
See the accompanying AUTHORS file for a complete list of authors.
This file is subject to the terms and conditions defined in LICENSE.
"""

from .analyzer import FileAnalyzer
from .rules import BlankLineRuleEngine


class FileProcessor:
  """Handles file processing with change detection"""

  @staticmethod
  def processFile(filepath, checkOnly=False, returnDetails=False):
    """Process file and return True if changes were needed
    :param filepath: Path to file to process
    :type filepath: Path
    :param checkOnly: If True, only check if changes needed without writing
    :type checkOnly: bool
    :param returnDetails: If True, return (changed, summary) tuple
    :type returnDetails: bool
    :rtype: bool or tuple[bool, str]
    """

    try:
      with open(filepath, encoding='utf-8') as f:
        originalLines = f.readlines()
    except UnicodeDecodeError as e:
      print(f'Encoding error reading {filepath}: {e}. Try specifying encoding or convert to UTF-8.')

      return False
    except FileNotFoundError:
      print(f'File not found: {filepath}')

      return False
    except PermissionError:
      print(f'Permission denied reading {filepath}')

      return False
    except Exception as e:
      print(f'Unexpected error reading {filepath}: {e}')

      return False

    # Pass 1: Analyze file structure
    analyzer = FileAnalyzer()
    statements = analyzer.analyzeFile(originalLines)

    # Pass 2: Determine blank line placement
    ruleEngine = BlankLineRuleEngine()
    blankLineCounts = ruleEngine.applyRules(statements)

    # Pass 3: Reconstruct file with correct blank line placement
    newLines = FileProcessor._reconstructFile(statements, blankLineCounts, originalLines)

    # Check if content changed
    if newLines == originalLines:
      return (False, None) if returnDetails else False

    # Generate details if requested
    summary = None
    diff = None

    if returnDetails:
      summary = FileProcessor._generateChangeSummary(originalLines, newLines)
      diff = FileProcessor._generateDiff(originalLines, newLines, filepath)

    # Handle check-only mode
    if checkOnly:
      if returnDetails:
        return (True, (summary, diff))
      else:
        return True

    # Write changes to file atomically
    import os
    import tempfile

    try:
      # Write to temporary file first
      tempFile = None

      with tempfile.NamedTemporaryFile(
        mode='w', encoding='utf-8', dir=filepath.parent, prefix=f'.{filepath.name}.tmp', delete=False
      ) as f:
        tempFile = f.name

        f.writelines(newLines)

      # Atomically replace original with temporary file
      os.replace(tempFile, filepath)

      if returnDetails:
        return (True, (summary, diff))
      else:
        return True
    except Exception as e:
      # Clean up temp file if it exists
      if tempFile and os.path.exists(tempFile):
        try:
          os.unlink(tempFile)
        except Exception:
          pass

      print(f'Error writing {filepath}: {e}')

      if returnDetails:
        return (False, None)
      else:
        return False

  @staticmethod
  def _reconstructFile(statements, blankLineCounts, originalLines):
    """Reconstruct file content with correct blank line placement
    :param statements: List of parsed statements
    :type statements: list[Statement]
    :param blankLineCounts: Number of blank lines to add before each statement
    :type blankLineCounts: list[int]
    :param originalLines: Original file lines to preserve trailing newline behavior
    :type originalLines: list[str]
    :rtype: list[str]
    """

    newLines = []

    for i, stmt in enumerate(statements):
      # Skip existing blank lines - we'll add them back where they should be
      if stmt.isBlank:
        continue

      # Add blank lines before this statement if rules specify them
      if i < len(blankLineCounts):
        for _ in range(blankLineCounts[i]):
          newLines.append('\n')

      # Add the statement content
      newLines.extend(stmt.lines)

    # Preserve original file's trailing newline behavior
    if originalLines and newLines:
      originalEndsWithNewline = originalLines[-1].endswith('\n')
      newEndsWithNewline = newLines[-1].endswith('\n')

      if originalEndsWithNewline and not newEndsWithNewline:
        # Original had trailing newline, new doesn't - add it
        newLines[-1] = newLines[-1] + '\n'
      elif not originalEndsWithNewline and newEndsWithNewline:
        # Original had no trailing newline, new does - remove it
        newLines[-1] = newLines[-1].rstrip('\n')
      else:
        # Trailing newline behavior already matches - no change needed
        pass

    return newLines

  @staticmethod
  def _generateChangeSummary(originalLines, newLines):
    """Generate a summary of changes between original and new lines
    :param originalLines: Original file lines
    :type originalLines: list[str]
    :param newLines: New file lines
    :type newLines: list[str]
    :rtype: str
    """

    originalBlankCount = sum(1 for line in originalLines if line.strip() == '')
    newBlankCount = sum(1 for line in newLines if line.strip() == '')
    diff = newBlankCount - originalBlankCount

    if diff > 0:
      return f'added {diff} blank line{"s" if diff != 1 else ""}'
    elif diff < 0:
      return f'removed {-diff} blank line{"s" if diff != -1 else ""}'
    else:
      return 'rearranged blank lines'

  @staticmethod
  def _generateDiff(originalLines, newLines, filepath):
    """Generate a unified diff showing changes between original and new lines
    :param originalLines: Original file lines
    :type originalLines: list[str]
    :param newLines: New file lines
    :type newLines: list[str]
    :param filepath: Path to file for diff header
    :type filepath: Path
    :rtype: str
    """

    import datetime
    import difflib

    timestamp = datetime.datetime.now().isoformat()
    diff = difflib.unified_diff(
      originalLines, newLines, fromfile=f'{filepath} (original)', tofile=f'{filepath} (formatted)', lineterm=''
    )

    return '\n'.join(diff)
