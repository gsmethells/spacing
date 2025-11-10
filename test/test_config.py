"""
Unit tests for configuration system.
Copyright (c) 2025-2026 Greg Smethells. All rights reserved.
See the accompanying AUTHORS file for a complete list of authors.
This file is subject to the terms and conditions defined in LICENSE.
"""

import pytest
import tempfile
from pathlib import Path
from spacing.config import BlankLineConfig
from spacing.types import BlockType


class TestBlankLineConfig:
  def testFromDefaults(self):
    """Test default configuration creation"""

    config = BlankLineConfig.fromDefaults()

    assert config.defaultBetweenDifferent == 1
    assert config.consecutiveControl == 1
    assert config.consecutiveDefinition == 1
    assert config.afterDocstring == 1
    assert len(config.transitions) == 0

  def testGetBlankLinesSameType(self):
    """Test blank lines for same block types"""

    config = BlankLineConfig.fromDefaults()

    # Same type (non-special) should return 0
    assert config.getBlankLines(BlockType.ASSIGNMENT, BlockType.ASSIGNMENT) == 0
    assert config.getBlankLines(BlockType.CALL, BlockType.CALL) == 0
    assert config.getBlankLines(BlockType.IMPORT, BlockType.IMPORT) == 0

    # Special consecutive rules
    assert config.getBlankLines(BlockType.CONTROL, BlockType.CONTROL) == 1
    assert config.getBlankLines(BlockType.DEFINITION, BlockType.DEFINITION) == 1

  def testGetBlankLinesDifferentTypes(self):
    """Test blank lines for different block types"""

    config = BlankLineConfig.fromDefaults()

    # Different types should use default
    assert config.getBlankLines(BlockType.ASSIGNMENT, BlockType.CALL) == 1
    assert config.getBlankLines(BlockType.IMPORT, BlockType.CONTROL) == 1
    assert config.getBlankLines(BlockType.DEFINITION, BlockType.ASSIGNMENT) == 1

  def testGetBlankLinesWithOverrides(self):
    """Test blank lines with transition overrides"""

    config = BlankLineConfig(
      defaultBetweenDifferent=2,
      transitions={(BlockType.ASSIGNMENT, BlockType.CALL): 0, (BlockType.IMPORT, BlockType.ASSIGNMENT): 3},
      consecutiveControl=2,
    )

    # Override should be used
    assert config.getBlankLines(BlockType.ASSIGNMENT, BlockType.CALL) == 0
    assert config.getBlankLines(BlockType.IMPORT, BlockType.ASSIGNMENT) == 3

    # Default should be used for non-overridden
    assert config.getBlankLines(BlockType.CALL, BlockType.IMPORT) == 2

    # Special rule should be used
    assert config.getBlankLines(BlockType.CONTROL, BlockType.CONTROL) == 2

  def testFromTomlMinimal(self):
    """Test loading minimal TOML configuration"""

    tomlContent = """
[blank_lines]
default_between_different = 2
"""

    with tempfile.NamedTemporaryFile(mode='w', suffix='.toml', delete=False) as f:
      f.write(tomlContent)
      f.flush()

      config = BlankLineConfig.fromToml(Path(f.name))

    assert config.defaultBetweenDifferent == 2
    assert config.consecutiveControl == 1  # Default
    assert config.consecutiveDefinition == 1  # Default
    assert config.afterDocstring == 1  # Default
    assert len(config.transitions) == 0

  def testFromTomlComplete(self):
    """Test loading complete TOML configuration"""

    tomlContent = """
[blank_lines]
default_between_different = 0
consecutive_control = 2
consecutive_definition = 3
after_docstring = 0
assignment_to_call = 1
call_to_assignment = 2
import_to_definition = 0
"""

    with tempfile.NamedTemporaryFile(mode='w', suffix='.toml', delete=False) as f:
      f.write(tomlContent)
      f.flush()

      config = BlankLineConfig.fromToml(Path(f.name))

    assert config.defaultBetweenDifferent == 0
    assert config.consecutiveControl == 2
    assert config.consecutiveDefinition == 3
    assert config.afterDocstring == 0

    expected = {
      (BlockType.ASSIGNMENT, BlockType.CALL): 1,
      (BlockType.CALL, BlockType.ASSIGNMENT): 2,
      (BlockType.IMPORT, BlockType.DEFINITION): 0,
    }

    assert config.transitions == expected

  def testFromTomlValidationErrors(self):
    """Test TOML validation errors"""

    # Invalid range
    tomlContent = """
[blank_lines]
default_between_different = 5
"""

    with tempfile.NamedTemporaryFile(mode='w', suffix='.toml', delete=False) as f:
      f.write(tomlContent)
      f.flush()

      with pytest.raises(ValueError, match='must be between 0 and 3'):
        BlankLineConfig.fromToml(Path(f.name))

  def testFromTomlInvalidBlockType(self):
    """Test TOML with invalid block type names"""

    tomlContent = """
[blank_lines]
invalid_to_call = 1
"""

    with tempfile.NamedTemporaryFile(mode='w', suffix='.toml', delete=False) as f:
      f.write(tomlContent)
      f.flush()

      with pytest.raises(ValueError, match='Unknown block type: invalid'):
        BlankLineConfig.fromToml(Path(f.name))

  def testFromTomlInvalidTransitionFormat(self):
    """Test TOML with invalid transition format"""

    tomlContent = """
[blank_lines]
assignment_call = 1
"""

    with tempfile.NamedTemporaryFile(mode='w', suffix='.toml', delete=False) as f:
      f.write(tomlContent)
      f.flush()

      with pytest.raises(ValueError, match='Invalid transition key format'):
        BlankLineConfig.fromToml(Path(f.name))

  def testFromTomlFileNotFound(self):
    """Test TOML file not found error"""

    with pytest.raises(FileNotFoundError):
      BlankLineConfig.fromToml(Path('/nonexistent/file.toml'))

  def testFromTomlInvalidToml(self):
    """Test invalid TOML syntax"""

    tomlContent = """
[blank_lines
invalid toml syntax
"""

    with tempfile.NamedTemporaryFile(mode='w', suffix='.toml', delete=False) as f:
      f.write(tomlContent)
      f.flush()

      with pytest.raises(ValueError, match='Failed to parse TOML'):
        BlankLineConfig.fromToml(Path(f.name))

  def testParseBlockType(self):
    """Test block type parsing"""

    assert BlankLineConfig._parseBlockType('assignment') == BlockType.ASSIGNMENT
    assert BlankLineConfig._parseBlockType('call') == BlockType.CALL
    assert BlankLineConfig._parseBlockType('import') == BlockType.IMPORT
    assert BlankLineConfig._parseBlockType('control') == BlockType.CONTROL
    assert BlankLineConfig._parseBlockType('definition') == BlockType.DEFINITION
    assert BlankLineConfig._parseBlockType('declaration') == BlockType.DECLARATION
    assert BlankLineConfig._parseBlockType('comment') == BlockType.COMMENT

    with pytest.raises(ValueError, match='Unknown block type: invalid'):
      BlankLineConfig._parseBlockType('invalid')

  def testValidateBlankLineCount(self):
    """Test blank line count validation"""

    # Valid values
    BlankLineConfig._validateBlankLineCount(0, 'test')
    BlankLineConfig._validateBlankLineCount(1, 'test')
    BlankLineConfig._validateBlankLineCount(3, 'test')

    # Invalid values
    with pytest.raises(ValueError, match='must be between 0 and 3'):
      BlankLineConfig._validateBlankLineCount(-1, 'test')

    with pytest.raises(ValueError, match='must be between 0 and 3'):
      BlankLineConfig._validateBlankLineCount(4, 'test')

    with pytest.raises(ValueError, match='must be an integer'):
      BlankLineConfig._validateBlankLineCount('1', 'test')

  def testAllBlockTypeCombinations(self):
    """Test all valid block type combinations"""

    blockTypes = [
      BlockType.ASSIGNMENT,
      BlockType.CALL,
      BlockType.IMPORT,
      BlockType.CONTROL,
      BlockType.DEFINITION,
      BlockType.DECLARATION,
      BlockType.COMMENT,
    ]
    config = BlankLineConfig.fromDefaults()

    # Test all combinations don't crash
    for fromBlock in blockTypes:
      for toBlock in blockTypes:
        result = config.getBlankLines(fromBlock, toBlock)

        assert isinstance(result, int)
        assert 0 <= result <= 3

  def testAfterDocstringConfiguration(self):
    """Test afterDocstring configuration controls blank lines after docstrings"""

    # Default: 1 blank line after docstring (PEP 257)
    configDefault = BlankLineConfig.fromDefaults()

    assert configDefault.getBlankLines(BlockType.DOCSTRING, BlockType.CALL) == 1
    assert configDefault.getBlankLines(BlockType.DOCSTRING, BlockType.ASSIGNMENT) == 1
    assert configDefault.getBlankLines(BlockType.DOCSTRING, BlockType.DEFINITION) == 1

    # Configured: 0 blank lines after docstring (compact style)
    configCompact = BlankLineConfig(afterDocstring=0)

    assert configCompact.getBlankLines(BlockType.DOCSTRING, BlockType.CALL) == 0
    assert configCompact.getBlankLines(BlockType.DOCSTRING, BlockType.ASSIGNMENT) == 0
    assert configCompact.getBlankLines(BlockType.DOCSTRING, BlockType.DEFINITION) == 0

    # Docstring to docstring should not use afterDocstring
    assert configDefault.getBlankLines(BlockType.DOCSTRING, BlockType.DOCSTRING) == 0
    assert configCompact.getBlankLines(BlockType.DOCSTRING, BlockType.DOCSTRING) == 0
