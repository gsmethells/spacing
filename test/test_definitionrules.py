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

  def test_needsBlankAfterDefinitionClassDocstring(self):
    """Test needsBlankAfterDefinition returns 1 for class definition followed by docstring (PEP 257)"""

    handler = DefinitionRuleHandler()
    statements = [
      createStatement(BlockType.DEFINITION, 0, lines=['class Foo:']),
      createStatement(BlockType.DOCSTRING, 2),
    ]
    result = handler.needsBlankAfterDefinition(statements[0], statements[1], statements, 0)

    assert result == 1

  def test_needsBlankAfterDefinitionClassDocstringWithBlank(self):
    """Test needsBlankAfterDefinition returns 1 when blank line separates class def from docstring

    Covers the branch where blank lines are skipped during backward scan for class docstring detection.
    """

    handler = DefinitionRuleHandler()
    blankStmt = Statement(
      lines=[''], startLineIndex=1, endLineIndex=1, blockType=BlockType.ASSIGNMENT, indentLevel=-1, isBlank=True
    )
    statements = [
      createStatement(BlockType.DEFINITION, 0, lines=['class Foo:']),
      blankStmt,
      createStatement(BlockType.DOCSTRING, 2),
    ]
    result = handler.needsBlankAfterDefinition(statements[0], statements[2], statements, 0)

    assert result == 1

  def test_needsBlankAfterDefinitionFunctionDocstring(self):
    """Test needsBlankAfterDefinition for function def followed by docstring (not class docstring)"""

    handler = DefinitionRuleHandler()
    statements = [
      createStatement(BlockType.DEFINITION, 0, lines=['def foo():']),
      createStatement(BlockType.DOCSTRING, 2),
    ]
    result = handler.needsBlankAfterDefinition(statements[0], statements[1], statements, 0)

    assert result == 1

  def test_needsBlankAfterDefinitionClassFollowedByAssignment(self):
    """Test needsBlankAfterDefinition for class def followed by assignment (not a docstring)"""

    handler = DefinitionRuleHandler()
    statements = [
      createStatement(BlockType.DEFINITION, 0, lines=['class Foo:']),
      createStatement(BlockType.ASSIGNMENT, 2),
    ]
    result = handler.needsBlankAfterDefinition(statements[0], statements[1], statements, 0)

    assert result == 1

  def test_needsBlankAfterBlockTypeModuleLevelDocstring(self):
    """Test needsBlankAfterBlockType returns 1 for module-level docstring followed by code"""

    handler = DefinitionRuleHandler()
    statements = [
      createStatement(BlockType.DOCSTRING, 0),  # Module-level docstring
      createStatement(BlockType.IMPORT, 0),  # import statement
    ]
    result = handler.needsBlankAfterBlockType(BlockType.DOCSTRING, statements[1], statements, 0)

    assert result == 1

  def test_needsBlankAfterBlockTypeModuleLevelDocstringWithBlanksAndComments(self):
    """Test needsBlankAfterBlockType returns 1 for module-level docstring preceded by blanks and comments"""

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
      createStatement(BlockType.IMPORT, 0),  # import statement
    ]
    result = handler.needsBlankAfterBlockType(BlockType.DOCSTRING, statements[3], statements, 2)

    assert result == 1

  def test_needsBlankAfterBlockTypeDocstringWithCodeBefore(self):
    """Test needsBlankAfterBlockType for docstring that is not module-level due to code before it"""

    handler = DefinitionRuleHandler()
    statements = [
      createStatement(BlockType.ASSIGNMENT, 0),  # x = 1
      createStatement(BlockType.DOCSTRING, 0),  # Not module-level
      createStatement(BlockType.ASSIGNMENT, 0),  # y = 2
    ]
    result = handler.needsBlankAfterBlockType(BlockType.DOCSTRING, statements[2], statements, 1)

    assert result == 1

  def test_needsBlankAfterBlockTypeAssignment(self):
    """Test needsBlankAfterBlockType for assignment block type (not a docstring)"""

    handler = DefinitionRuleHandler()
    statements = [
      createStatement(BlockType.ASSIGNMENT, 0),
      createStatement(BlockType.CALL, 0),
    ]
    result = handler.needsBlankAfterBlockType(BlockType.ASSIGNMENT, statements[1], statements, 0)

    assert result == 1
