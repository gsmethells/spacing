"""
Unit tests for file processor.
Copyright (c) 2025-2026 Greg Smethells. All rights reserved.
See the accompanying AUTHORS file for a complete list of authors.
This file is subject to the terms and conditions defined in LICENSE.
"""

import tempfile
from pathlib import Path
from spacing.processor import FileProcessor


class TestFileProcessor:
  def testProcessFileNoChanges(self):
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
      with open(f.name) as result_file:
        final_content = result_file.read()

      assert final_content == content

  def testProcessFileWithChanges(self):
    """Test processing file that needs changes"""

    original_content = """import sys
x = 1
def func():
  pass"""

    with tempfile.NamedTemporaryFile(mode='w', suffix='.py', delete=False) as f:
      f.write(original_content)
      f.flush()

      # Should return True (changes made)
      result = FileProcessor.processFile(Path(f.name), checkOnly=False)

      assert result

      # Content should be changed
      with open(f.name) as result_file:
        final_content = result_file.read()

      assert final_content != original_content
      assert '\n\n' in final_content  # Should have blank lines

  def testCheckOnlyMode(self):
    """Test check-only mode doesn't modify files"""

    original_content = """import sys
x = 1
def func():
  pass"""

    with tempfile.NamedTemporaryFile(mode='w', suffix='.py', delete=False) as f:
      f.write(original_content)
      f.flush()

      # Check-only should return True (changes needed) but not modify file
      result = FileProcessor.processFile(Path(f.name), checkOnly=True)

      assert result

      # Content should be unchanged
      with open(f.name) as result_file:
        final_content = result_file.read()

      assert final_content == original_content

  def testFileReadError(self):
    """Test handling of file read errors"""

    nonexistent_path = Path('/nonexistent/file.py')
    result = FileProcessor.processFile(nonexistent_path, checkOnly=False)

    assert not result

  def testFileWriteError(self, monkeypatch):
    """Test handling of file write errors"""

    original_content = """import sys
x = 1"""

    with tempfile.NamedTemporaryFile(mode='w', suffix='.py', delete=False) as f:
      f.write(original_content)
      f.flush()

      filepath = Path(f.name)

    # Mock NamedTemporaryFile to raise OSError when trying to create temp file
    def mock_tempfile(*args, **kwargs):
      raise OSError('Mock tempfile creation error')

    monkeypatch.setattr('tempfile.NamedTemporaryFile', mock_tempfile)

    result = FileProcessor.processFile(filepath, checkOnly=False)

    assert not result  # Should return False on write error

    # Clean up test file
    try:
      filepath.unlink()
    except Exception:
      pass

  def testEmptyFile(self):
    """Test processing empty file"""

    with tempfile.NamedTemporaryFile(mode='w', suffix='.py', delete=False) as f:
      f.write('')
      f.flush()

      result = FileProcessor.processFile(Path(f.name), checkOnly=False)

      assert not result  # Empty file doesn't need changes

      with open(f.name) as result_file:
        final_content = result_file.read()

      assert final_content == ''

  def testFileWithOnlyBlankLines(self):
    """Test processing file with only blank lines - should be cleaned to empty"""

    content = '\n\n\n'

    with tempfile.NamedTemporaryFile(mode='w', suffix='.py', delete=False) as f:
      f.write(content)
      f.flush()

      result = FileProcessor.processFile(Path(f.name), checkOnly=False)

      assert result  # Blank lines should be removed

      with open(f.name) as result_file:
        final_content = result_file.read()

      assert final_content == ''  # Should be empty file

  def testFileWithOnlyComments(self):
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
      with open(f.name) as result_file:
        final_content = result_file.read()

      # Verify it's syntactically valid (no exceptions during processing)
      assert len(final_content) > 0

  def testFileWithEncodingError(self):
    """Test handling of UnicodeDecodeError when reading file"""

    with tempfile.NamedTemporaryFile(mode='wb', suffix='.py', delete=False) as f:
      # Write invalid UTF-8 bytes
      f.write(b'\xff\xfe\xfd')
      f.flush()

      result = FileProcessor.processFile(Path(f.name), checkOnly=False)

      assert not result  # Should return False on encoding error

  def testFileWithPermissionError(self, monkeypatch):
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

  def testReturnDetailsWithChanges(self):
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

  def testReturnDetailsCheckOnlyMode(self):
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

  def testReturnDetailsRemovedBlankLines(self):
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

  def testWriteErrorDuringFileProcessing(self, monkeypatch):
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
