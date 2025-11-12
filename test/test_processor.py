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

      # Mock open to raise an exception on write
      def mock_open(*args, **kwargs):
        if 'w' in args[1]:  # Write mode
          raise OSError('Mock write error')

        return open(*args, **kwargs)

      monkeypatch.setattr('builtins.open', mock_open)

      result = FileProcessor.processFile(Path(f.name), checkOnly=False)

      assert not result  # Should return False on write error

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
