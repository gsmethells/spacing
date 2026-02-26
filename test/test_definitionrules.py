"""
Unit tests for definition rule handler.
Copyright (c) 2025-2026 Greg Smethells. All rights reserved.
See the accompanying AUTHORS file for a complete list of authors.
This file is subject to the terms and conditions defined in LICENSE.
"""

from spacing.definitionrules import DefinitionRuleHandler
from spacing.types import BlockType, Statement


def createStatement(blockType, indentLevel, lines=None):
  """Helper to create test statements"""

  if lines is None:
    lines = ['test']

  return Statement(
    lines=lines,
    startLineIndex=0,
    endLineIndex=0,
    blockType=blockType,
    indentLevel=indentLevel,
  )


class TestDefinitionRuleHandler:
  """Test suite for DefinitionRuleHandler class"""

  def test_needsBlankAfterDefinitionBasic(self):
    """Test needsBlankAfterDefinition returns value from config"""

    handler = DefinitionRuleHandler()
    prevStmt = createStatement(BlockType.DEFINITION, 0)
    currentStmt = createStatement(BlockType.ASSIGNMENT, 0)

    result = handler.needsBlankAfterDefinition(prevStmt, currentStmt, [], 0)

    assert result >= 0  # Should return config value

  def test_needsBlankAfterControlBasic(self):
    """Test needsBlankAfterControl returns value from config"""

    handler = DefinitionRuleHandler()
    currentStmt = createStatement(BlockType.ASSIGNMENT, 0)

    result = handler.needsBlankAfterControl(currentStmt)

    assert result >= 0  # Should return config value

  def test_needsBlankAfterBlockTypeBasic(self):
    """Test needsBlankAfterBlockType returns value from config"""

    handler = DefinitionRuleHandler()
    currentStmt = createStatement(BlockType.ASSIGNMENT, 0)

    result = handler.needsBlankAfterBlockType(BlockType.IMPORT, currentStmt, [], 0)

    assert result >= 0  # Should return config value

  def test_isClassDocstringTrue(self):
    """Test _isClassDocstring detects class docstring"""

    handler = DefinitionRuleHandler()
    statements = [
      createStatement(BlockType.DEFINITION, 0, lines=['class Foo:']),
      createStatement(BlockType.DOCSTRING, 2),
    ]

    result = handler._isClassDocstring(statements, 1, BlockType.DOCSTRING)

    assert result is True

  def test_isClassDocstringFalseNotClass(self):
    """Test _isClassDocstring returns False for function docstring"""

    handler = DefinitionRuleHandler()
    statements = [
      createStatement(BlockType.DEFINITION, 0, lines=['def foo():']),
      createStatement(BlockType.DOCSTRING, 2),
    ]

    result = handler._isClassDocstring(statements, 1, BlockType.DOCSTRING)

    assert result is False

  def test_isClassDocstringFalseNotDocstring(self):
    """Test _isClassDocstring returns False when not a docstring"""

    handler = DefinitionRuleHandler()
    statements = [
      createStatement(BlockType.DEFINITION, 0, lines=['class Foo:']),
      createStatement(BlockType.ASSIGNMENT, 2),
    ]

    result = handler._isClassDocstring(statements, 1, BlockType.ASSIGNMENT)

    assert result is False

  def test_isClassDocstringFalseNoneIndex(self):
    """Test _isClassDocstring returns False when index is None"""

    handler = DefinitionRuleHandler()
    statements = []

    result = handler._isClassDocstring(statements, None, BlockType.DOCSTRING)

    assert result is False

  def test_isModuleLevelDocstringTrue(self):
    """Test _isModuleLevelDocstring detects module-level docstring"""

    handler = DefinitionRuleHandler()
    statements = [
      createStatement(BlockType.DOCSTRING, 0),  # First statement
    ]

    result = handler._isModuleLevelDocstring(statements, 0, BlockType.DOCSTRING)

    assert result is True

  def test_isModuleLevelDocstringTrueWithBlanksAndComments(self):
    """Test _isModuleLevelDocstring detects module-level docstring with blanks/comments before"""

    handler = DefinitionRuleHandler()
    statements = [
      Statement(lines=[], startLineIndex=0, endLineIndex=0, blockType=BlockType.COMMENT, indentLevel=0, isBlank=True),
      Statement(
        lines=['# comment'],
        startLineIndex=1,
        endLineIndex=1,
        blockType=BlockType.COMMENT,
        indentLevel=0,
        isComment=True,
      ),
      createStatement(BlockType.DOCSTRING, 0),  # Module-level docstring
    ]

    result = handler._isModuleLevelDocstring(statements, 2, BlockType.DOCSTRING)

    assert result is True

  def test_isModuleLevelDocstringFalseCodeBefore(self):
    """Test _isModuleLevelDocstring returns False when code exists before docstring"""

    handler = DefinitionRuleHandler()
    statements = [
      createStatement(BlockType.ASSIGNMENT, 0),  # x = 1
      createStatement(BlockType.DOCSTRING, 0),  # Not module-level
    ]

    result = handler._isModuleLevelDocstring(statements, 1, BlockType.DOCSTRING)

    assert result is False

  def test_isModuleLevelDocstringFalseNotDocstring(self):
    """Test _isModuleLevelDocstring returns False when not a docstring"""

    handler = DefinitionRuleHandler()
    statements = [
      createStatement(BlockType.ASSIGNMENT, 0),
    ]

    result = handler._isModuleLevelDocstring(statements, 0, BlockType.ASSIGNMENT)

    assert result is False

  def test_isModuleLevelDocstringFalseNoneIndex(self):
    """Test _isModuleLevelDocstring returns False when index is None"""

    handler = DefinitionRuleHandler()
    statements = []

    result = handler._isModuleLevelDocstring(statements, None, BlockType.DOCSTRING)

    assert result is False
