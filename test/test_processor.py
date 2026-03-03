"""
Unit tests for file processor.
Copyright (c) 2025-2026 Greg Smethells. All rights reserved.
See the accompanying AUTHORS file for a complete list of authors.
This file is subject to the terms and conditions defined in LICENSE.
"""

import tempfile
from pathlib import Path
from spacing.processor import FileProcessor
from spacing.types import BlockType


class TestFileProcessor:
  def test_processFileNoChanges(self):
    """Test processing file that doesn't need changes"""

    # Create a perfectly formatted file (PEP 8 compliant)
    content = """import sys

x = 1


def func():
  pass
"""

    with tempfile.NamedTemporaryFile(mode='w', suffix='.py', delete=False) as f:
      f.write(content)
      f.flush()

      # Should return False (no changes needed)
      result = FileProcessor.processFile(Path(f.name), checkOnly=False)

      assert not result

      # Content should remain unchanged
      with open(f.name) as resultFile:
        finalContent = resultFile.read()

      assert finalContent == content

  def test_processFileWithChanges(self):
    """Test processing file that needs changes"""

    originalContent = """import sys
x = 1
def func():
  pass"""

    with tempfile.NamedTemporaryFile(mode='w', suffix='.py', delete=False) as f:
      f.write(originalContent)
      f.flush()

      # Should return True (changes made)
      result = FileProcessor.processFile(Path(f.name), checkOnly=False)

      assert result

      # Content should be changed
      with open(f.name) as resultFile:
        finalContent = resultFile.read()

      assert finalContent != originalContent
      assert '\n\n' in finalContent  # Should have blank lines

  def test_checkOnlyMode(self):
    """Test check-only mode doesn't modify files"""

    originalContent = """import sys
x = 1
def func():
  pass"""

    with tempfile.NamedTemporaryFile(mode='w', suffix='.py', delete=False) as f:
      f.write(originalContent)
      f.flush()

      # Check-only should return True (changes needed) but not modify file
      result = FileProcessor.processFile(Path(f.name), checkOnly=True)

      assert result

      # Content should be unchanged
      with open(f.name) as resultFile:
        finalContent = resultFile.read()

      assert finalContent == originalContent

  def test_fileReadError(self):
    """Test handling of file read errors"""

    nonexistentPath = Path('/nonexistent/file.py')
    result = FileProcessor.processFile(nonexistentPath, checkOnly=False)

    assert not result

  def test_fileWriteError(self, monkeypatch):
    """Test handling of file write errors"""

    originalContent = """import sys
x = 1"""

    with tempfile.NamedTemporaryFile(mode='w', suffix='.py', delete=False) as f:
      f.write(originalContent)
      f.flush()

      filepath = Path(f.name)

    # Mock NamedTemporaryFile to raise OSError when trying to create temp file
    def mockTempfile(*args, **kwargs):
      raise OSError('Mock tempfile creation error')

    monkeypatch.setattr('tempfile.NamedTemporaryFile', mockTempfile)

    result = FileProcessor.processFile(filepath, checkOnly=False)

    assert not result  # Should return False on write error

    # Clean up test file
    try:
      filepath.unlink()
    except Exception:
      pass

  def test_emptyFile(self):
    """Test processing empty file"""

    with tempfile.NamedTemporaryFile(mode='w', suffix='.py', delete=False) as f:
      f.write('')
      f.flush()

      result = FileProcessor.processFile(Path(f.name), checkOnly=False)

      assert not result  # Empty file doesn't need changes

      with open(f.name) as resultFile:
        finalContent = resultFile.read()

      assert finalContent == ''

  def test_fileWithOnlyBlankLines(self):
    """Test processing file with only blank lines - should be cleaned to empty"""

    content = '\n\n\n'

    with tempfile.NamedTemporaryFile(mode='w', suffix='.py', delete=False) as f:
      f.write(content)
      f.flush()

      result = FileProcessor.processFile(Path(f.name), checkOnly=False)

      assert result  # Blank lines should be removed

      with open(f.name) as resultFile:
        finalContent = resultFile.read()

      assert finalContent == ''  # Should be empty file

  def test_fileWithOnlyComments(self):
    """Test processing file with only comments"""

    content = """# Header comment

# Another comment
# Final comment
"""

    with tempfile.NamedTemporaryFile(mode='w', suffix='.py', delete=False) as f:
      f.write(content)
      f.flush()

      # Comments alone typically don't need blank lines between them

      result = FileProcessor.processFile(Path(f.name), checkOnly=False)

      # This depends on our comment rules implementation
      with open(f.name) as resultFile:
        finalContent = resultFile.read()

      # Verify it's syntactically valid (no exceptions during processing)
      assert len(finalContent) > 0

  def test_fileWithEncodingError(self):
    """Test handling of UnicodeDecodeError when reading file"""

    with tempfile.NamedTemporaryFile(mode='wb', suffix='.py', delete=False) as f:
      # Write invalid UTF-8 bytes
      f.write(b'\xff\xfe\xfd')
      f.flush()

      result = FileProcessor.processFile(Path(f.name), checkOnly=False)

      assert not result  # Should return False on encoding error

  def test_fileWithPermissionError(self, monkeypatch):
    """Test handling of PermissionError when reading file"""

    import builtins

    def mockOpen(*args, **kwargs):
      raise PermissionError('Permission denied')

    with tempfile.NamedTemporaryFile(mode='w', suffix='.py', delete=False) as f:
      f.write('x = 1')
      f.flush()

      # Mock open to raise PermissionError
      monkeypatch.setattr(builtins, 'open', mockOpen)

      result = FileProcessor.processFile(Path(f.name), checkOnly=False)

      assert not result  # Should return False on permission error

  def test_returnDetailsWithChanges(self):
    """Test returnDetails parameter returns summary and diff when changes are made"""

    content = """import sys
x = 1
y = 2"""
    expected = """import sys

x = 1
y = 2"""

    with tempfile.NamedTemporaryFile(mode='w', suffix='.py', delete=False) as f:
      f.write(content)
      f.flush()

      changed, (summary, diff) = FileProcessor.processFile(Path(f.name), checkOnly=False, returnDetails=True)

      assert changed
      assert summary is not None
      assert diff is not None
      assert len(summary) > 0

  def test_returnDetailsCheckOnlyMode(self):
    """Test returnDetails parameter in checkOnly mode"""

    content = """import sys
x = 1
y = 2"""

    with tempfile.NamedTemporaryFile(mode='w', suffix='.py', delete=False) as f:
      f.write(content)
      f.flush()

      changed, (summary, diff) = FileProcessor.processFile(Path(f.name), checkOnly=True, returnDetails=True)

      assert changed
      assert summary is not None
      assert diff is not None

  def test_returnDetailsRemovedBlankLines(self):
    """Test returnDetails shows 'removed' when blank lines are deleted"""

    content = """import sys


x = 1"""
    expected = """import sys

x = 1"""

    with tempfile.NamedTemporaryFile(mode='w', suffix='.py', delete=False) as f:
      f.write(content)
      f.flush()

      changed, (summary, diff) = FileProcessor.processFile(Path(f.name), checkOnly=True, returnDetails=True)

      assert changed
      assert 'removed 1 blank line' in summary
      assert diff is not None

  def test_writeErrorDuringFileProcessing(self, monkeypatch):
    """Test that write errors during file processing are handled correctly"""

    import builtins
    import os

    content = """import sys
x = 1
y = 2"""

    with tempfile.NamedTemporaryFile(mode='w', suffix='.py', delete=False) as f:
      f.write(content)
      f.flush()

      filePath = Path(f.name)

    originalOpen = builtins.open

    def mockOpen(path, *args, **kwargs):
      # Allow reading original file
      if 'r' in args or kwargs.get('mode', '').startswith('r'):
        return originalOpen(path, *args, **kwargs)

      # Raise error when trying to write temp file
      raise OSError('Simulated write error')

    monkeypatch.setattr(builtins, 'open', mockOpen)

    # Should handle write error gracefully
    result = FileProcessor.processFile(filePath, checkOnly=False)

    assert not result  # Should return False on write error

    # Clean up
    try:
      os.unlink(filePath)
    except Exception:
      pass

  def test_writeErrorWithReturnDetails(self, monkeypatch):
    """Test write error returns (False, None) when returnDetails is True"""

    import os

    content = """import sys
x = 1
y = 2"""

    with tempfile.NamedTemporaryFile(mode='w', suffix='.py', delete=False) as f:
      f.write(content)
      f.flush()

      filePath = Path(f.name)

    # Mock os.replace to simulate atomic write failure after temp file is created
    def mockReplace(*args, **kwargs):
      raise OSError('Simulated replace error')

    monkeypatch.setattr(os, 'replace', mockReplace)

    result = FileProcessor.processFile(filePath, checkOnly=False, returnDetails=True)

    assert result == (False, None)

    try:
      os.unlink(filePath)
    except Exception:
      pass

  def test_returnDetailsNoChanges(self):
    """Test returnDetails returns (False, None) when no changes needed"""

    content = """import sys

x = 1
"""

    with tempfile.NamedTemporaryFile(mode='w', suffix='.py', delete=False) as f:
      f.write(content)
      f.flush()

      result = FileProcessor.processFile(Path(f.name), checkOnly=True, returnDetails=True)

      assert result == (False, None)

  def test_rearrangedBlankLinesSummary(self):
    """Test summary says 'rearranged' when blank line count stays the same"""

    # We need a file where blank lines are moved but total count stays the same
    content = """import sys

x = 1
y = 2

z = 3
"""

    # This specific case may or may not result in rearranging — test via the static method directly
    originalLines = ['import sys\n', '\n', '\n', 'x = 1\n', 'y = 2\n']
    newLines = ['import sys\n', '\n', 'x = 1\n', '\n', 'y = 2\n']
    summary = FileProcessor._generateChangeSummary(originalLines, newLines)

    assert summary == 'rearranged blank lines'

  def test_generateChangeSummaryAdded(self):
    """Test summary says 'added' when blank lines are added"""

    originalLines = ['import sys\n', 'x = 1\n']
    newLines = ['import sys\n', '\n', 'x = 1\n']
    summary = FileProcessor._generateChangeSummary(originalLines, newLines)

    assert 'added 1 blank line' in summary

  def test_trailingNewlinePreservationAddNewline(self):
    """Test that trailing newline is added when original had one but new doesn't"""

    # Create file that ends with newline, where processing would remove it
    # Test via _reconstructFile directly
    from spacing.types import Statement

    statements = [
      Statement(
        lines=['x = 1'],
        startLineIndex=0,
        endLineIndex=0,
        blockType=BlockType.ASSIGNMENT,
        indentLevel=0,
      ),
    ]
    blankLineCounts = [0]
    originalLines = ['x = 1\n']
    result = FileProcessor._reconstructFile(statements, blankLineCounts, originalLines)

    assert result[-1].endswith('\n')

  def test_trailingNewlinePreservationRemoveNewline(self):
    """Test that trailing newline is removed when original didn't have one"""

    from spacing.types import Statement

    statements = [
      Statement(
        lines=['x = 1\n'],
        startLineIndex=0,
        endLineIndex=0,
        blockType=BlockType.ASSIGNMENT,
        indentLevel=0,
      ),
    ]
    blankLineCounts = [0]
    originalLines = ['x = 1']  # No trailing newline
    result = FileProcessor._reconstructFile(statements, blankLineCounts, originalLines)

    assert not result[-1].endswith('\n')
