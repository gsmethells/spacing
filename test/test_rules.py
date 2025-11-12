"""
Unit tests for blank line rule engine.
Copyright (c) 2025-2026 Greg Smethells. All rights reserved.
See the accompanying AUTHORS file for a complete list of authors.
This file is subject to the terms and conditions defined in LICENSE.
"""

from spacing.analyzer import FileAnalyzer
from spacing.config import BlankLineConfig, setConfig
from spacing.processor import FileProcessor
from spacing.rules import BlankLineRuleEngine
from spacing.types import BlockType, Statement


class TestBlankLineRuleEngine:
  def createStatement(self, blockType, indentLevel=0, isComment=False, isBlank=False, isSecondaryClause=False):
    """Helper to create test statements"""

    return Statement(
      lines=['dummy'],
      startLineIndex=0,
      endLineIndex=0,
      blockType=blockType,
      indentLevel=indentLevel,
      isComment=isComment,
      isBlank=isBlank,
      isSecondaryClause=isSecondaryClause,
    )

  def testSameBlockType(self):
    """Test no blank line between same block types (except Control/Definition)"""

    setConfig(BlankLineConfig.fromDefaults())

    engine = BlankLineRuleEngine()
    statements = [
      self.createStatement(BlockType.ASSIGNMENT),
      self.createStatement(BlockType.ASSIGNMENT),
    ]
    result = engine.applyRules(statements)

    assert result == [0, 0]

  def testDifferentBlockTypes(self):
    """Test blank line between different block types"""

    setConfig(BlankLineConfig.fromDefaults())

    engine = BlankLineRuleEngine()
    statements = [
      self.createStatement(BlockType.IMPORT),
      self.createStatement(BlockType.ASSIGNMENT),
    ]
    result = engine.applyRules(statements)

    assert result == [0, 1]  # Blank line before second statement

  def testConsecutiveControlBlocks(self):
    """Test consecutive Control blocks need separation"""

    setConfig(BlankLineConfig.fromDefaults())

    engine = BlankLineRuleEngine()
    statements = [
      self.createStatement(BlockType.CONTROL),
      self.createStatement(BlockType.CONTROL),
    ]
    result = engine.applyRules(statements)

    assert result == [0, 1]  # Blank line before second control block

  def testConsecutiveDefinitionBlocks(self):
    """Test consecutive Definition blocks at module level (PEP 8: 2 blank lines)"""

    setConfig(BlankLineConfig.fromDefaults())

    engine = BlankLineRuleEngine()
    statements = [
      self.createStatement(BlockType.DEFINITION, indentLevel=0),
      self.createStatement(BlockType.DEFINITION, indentLevel=0),
    ]
    result = engine.applyRules(statements)

    assert result == [0, 2]  # PEP 8: 2 blank lines at module level

  def testConsecutiveDefinitionBlocksNested(self):
    """Test consecutive Definition blocks inside class (PEP 8: 1 blank line)"""

    setConfig(BlankLineConfig.fromDefaults())

    engine = BlankLineRuleEngine()
    statements = [
      self.createStatement(BlockType.DEFINITION, indentLevel=2),
      self.createStatement(BlockType.DEFINITION, indentLevel=2),
    ]
    result = engine.applyRules(statements)

    assert result == [0, 1]  # PEP 8: 1 blank line inside class

  def testSecondaryClauseRule(self):
    """Test no blank line before secondary clauses"""

    setConfig(BlankLineConfig.fromDefaults())

    engine = BlankLineRuleEngine()
    statements = [
      self.createStatement(BlockType.CONTROL),  # if
      self.createStatement(BlockType.CONTROL, isSecondaryClause=True),  # else
    ]
    result = engine.applyRules(statements)

    assert result == [0, 0]  # No blank line before else

  def testCommentBreakRule(self):
    """Test blank line before comments (comment break rule)"""

    setConfig(BlankLineConfig.fromDefaults())

    engine = BlankLineRuleEngine()
    statements = [
      self.createStatement(BlockType.ASSIGNMENT),
      self.createStatement(BlockType.ASSIGNMENT, isComment=True),
    ]
    result = engine.applyRules(statements)

    assert result == [0, 1]  # Blank line before comment

  def testBlankLinesIgnored(self):
    """Test blank lines are ignored in rule processing"""

    setConfig(BlankLineConfig.fromDefaults())

    engine = BlankLineRuleEngine()
    statements = [
      self.createStatement(BlockType.ASSIGNMENT),
      self.createStatement(BlockType.ASSIGNMENT, isBlank=True),
      self.createStatement(BlockType.CALL),
    ]
    result = engine.applyRules(statements)

    assert result == [0, 0, 1]  # Blank line before CALL (different from ASSIGNMENT)

  def testIndentationLevelProcessing(self):
    """Test rules applied independently at each indentation level"""

    setConfig(BlankLineConfig.fromDefaults())

    engine = BlankLineRuleEngine()
    statements = [
      self.createStatement(BlockType.ASSIGNMENT, indentLevel=0),
      self.createStatement(BlockType.ASSIGNMENT, indentLevel=2),  # Nested
      self.createStatement(BlockType.CALL, indentLevel=2),  # Nested different type
      self.createStatement(BlockType.CALL, indentLevel=0),  # Back to level 0
    ]
    result = engine.applyRules(statements)

    # Level 0: ASSIGNMENT -> CALL (different types, need blank line)
    # Level 2: ASSIGNMENT -> CALL (different types, need blank line)
    assert result == [0, 0, 1, 1]

  def testNeedsBlankLineBetweenMethod(self):
    """Test private _needsBlankLineBetween method"""

    setConfig(BlankLineConfig.fromDefaults())

    engine = BlankLineRuleEngine()

    # Same types (except Control/Definition)
    assert not engine._needsBlankLineBetween(BlockType.ASSIGNMENT, BlockType.ASSIGNMENT)
    assert not engine._needsBlankLineBetween(BlockType.CALL, BlockType.CALL)
    assert not engine._needsBlankLineBetween(BlockType.IMPORT, BlockType.IMPORT)

    # Same Control/Definition types (special rule)
    assert engine._needsBlankLineBetween(BlockType.CONTROL, BlockType.CONTROL)
    assert engine._needsBlankLineBetween(BlockType.DEFINITION, BlockType.DEFINITION)

    # Different types
    assert engine._needsBlankLineBetween(BlockType.IMPORT, BlockType.ASSIGNMENT)
    assert engine._needsBlankLineBetween(BlockType.ASSIGNMENT, BlockType.CALL)

  def testEmptyStatements(self):
    """Test handling of empty statement list"""

    setConfig(BlankLineConfig.fromDefaults())

    engine = BlankLineRuleEngine()
    result = engine.applyRules([])

    assert result == []

  def testComplexScenario(self):
    """Test complex scenario with multiple rules"""

    setConfig(BlankLineConfig.fromDefaults())

    engine = BlankLineRuleEngine()
    statements = [
      self.createStatement(BlockType.IMPORT),  # 0: import
      self.createStatement(BlockType.IMPORT),  # 1: import (same type)
      self.createStatement(BlockType.ASSIGNMENT),  # 2: assignment (different type)
      self.createStatement(BlockType.ASSIGNMENT, isComment=True),  # 3: comment (comment break)
      self.createStatement(BlockType.CALL),  # 4: call (after comment)
      self.createStatement(BlockType.CONTROL),  # 5: if (different type)
      self.createStatement(BlockType.CONTROL, isSecondaryClause=True),  # 6: else (secondary clause)
      self.createStatement(BlockType.CONTROL),  # 7: another if (consecutive control)
    ]
    result = engine.applyRules(statements)
    expected = [
      0,  # 0: first statement
      0,  # 1: same type as previous (import)
      1,  # 2: different type (assignment after import)
      1,  # 3: comment break rule
      0,  # 4: after comment reset
      1,  # 5: different type (control after call)
      0,  # 6: secondary clause rule (no blank before else)
      1,  # 7: consecutive control blocks rule
    ]

    assert result == expected

  def testCommentBreakRuleRegression(self):
    """Regression test for comment break rule bug (original issue)"""

    setConfig(BlankLineConfig.fromDefaults())

    engine = BlankLineRuleEngine()
    statements = [
      self.createStatement(BlockType.ASSIGNMENT),
      self.createStatement(BlockType.ASSIGNMENT, isComment=True),
    ]
    result = engine.applyRules(statements)

    # Comment should get blank line despite same block type
    assert result == [0, 1]

  def testIndentationProcessingRegression(self):
    """Regression test for indentation level processing bug (original issue)"""

    setConfig(BlankLineConfig.fromDefaults())

    engine = BlankLineRuleEngine()
    statements = [
      self.createStatement(BlockType.ASSIGNMENT, indentLevel=0),
      self.createStatement(BlockType.ASSIGNMENT, indentLevel=2),  # Nested
      self.createStatement(BlockType.CALL, indentLevel=2),  # Nested different type
      self.createStatement(BlockType.CALL, indentLevel=0),  # Back to level 0
    ]
    result = engine.applyRules(statements)

    # Should get blank lines: none, none, different types at level 2, returning from nested
    assert result == [0, 0, 1, 1]

  def testCommentBlankLinePreservation(self):
    """Test that existing blank lines after comments are preserved (leave-as-is rule)"""

    setConfig(BlankLineConfig.fromDefaults())

    engine = BlankLineRuleEngine()
    statements = [
      # Copyright header scenario
      self.createStatement(BlockType.COMMENT, isComment=True),  # 0: # Copyright line 1
      self.createStatement(BlockType.COMMENT, isComment=True),  # 1: # Copyright line 2
      self.createStatement(BlockType.COMMENT, isComment=True),  # 2: # Copyright line 3
      self.createStatement(BlockType.CALL, isBlank=True),  # 3: blank line after comment
      self.createStatement(BlockType.IMPORT),  # 4: import statement
      self.createStatement(BlockType.ASSIGNMENT),  # 5: assignment statement
    ]
    result = engine.applyRules(statements)

    # Expected: no blank before comments, preserve existing blank after comment block
    # 0: first comment (no blank line)
    # 1: second comment (no blank line - same type)
    # 2: third comment (no blank line - same type)
    # 3: blank line (skipped in processing)
    # 4: import after comment block (should preserve existing blank line)
    # 5: assignment after import (different type)
    assert result == [0, 0, 0, 0, 1, 1]

  def testCommentWithoutBlankLineFollowing(self):
    """Test that no blank line is added after comment when none exists"""

    setConfig(BlankLineConfig.fromDefaults())

    engine = BlankLineRuleEngine()
    statements = [
      self.createStatement(BlockType.COMMENT, isComment=True),  # 0: comment
      self.createStatement(BlockType.IMPORT),  # 1: import (no blank between)
      self.createStatement(BlockType.ASSIGNMENT),  # 2: assignment
    ]
    result = engine.applyRules(statements)

    # Expected: no blank after comment when none exists originally
    # 0: first comment (no blank line)
    # 1: import after comment (no blank preserved since none existed)
    # 2: assignment after import (different type gets blank line)
    assert result == [0, 0, 1]

  def testBlankLineAfterTryExceptInFunctionBody(self):
    """Regression test: blank line should be added after try/except completes in function body"""

    setConfig(BlankLineConfig.fromDefaults())

    engine = BlankLineRuleEngine()
    statements = [
      self.createStatement(BlockType.DEFINITION, indentLevel=0),  # 0: def foo():
      self.createStatement(BlockType.CONTROL, indentLevel=2),  # 1: try:
      self.createStatement(BlockType.ASSIGNMENT, indentLevel=4),  # 2: x = 1
      self.createStatement(BlockType.CALL, indentLevel=2, isSecondaryClause=True),  # 3: except:
      self.createStatement(BlockType.CALL, indentLevel=4),  # 4: print(...)
      self.createStatement(BlockType.ASSIGNMENT, indentLevel=2),  # 5: y = 2
    ]
    result = engine.applyRules(statements)

    # Expected: blank line before statement after try/except completes
    # Statement 5 (y = 2) comes after the try/except CONTROL block completes
    # Since we're in a function body, CONTROL -> ASSIGNMENT should get a blank line
    assert result == [0, 0, 0, 0, 0, 1]

  def testCommentParagraphSeparationPreserved(self):
    """Regression: Blank lines between comment blocks (comment paragraphs) should be preserved"""

    import tempfile
    from pathlib import Path
    from spacing.processor import FileProcessor

    # Input with blank lines separating comment paragraphs
    input_code = """def setup():
  from catapult.lang.console import promptForAnswer, promptYesOrNo

  # Define the base environment variables

  # Stage
  if JOINTS_STAGE not in environ or environ[JOINTS_STAGE] not in STAGES:
    environ[JOINTS_STAGE] = promptForAnswer('What stage is this system currently in', STAGES, PRODUCTION)

  # Architecture check
  isProduction = environ[JOINTS_STAGE] == PRODUCTION
  cpuCount = getCPUCount()

  # XXX: Important implementation note goes here
  #
  # This comment block has multiple lines
  # but it's a single paragraph
  #

  # Define the default environment variable values
  # Any environment variable with a defined value will not be prompted for later
  defaults = {}
"""

    # Expected: preserve blank lines directly adjacent to comments only
    expected_code = """def setup():
  from catapult.lang.console import promptForAnswer, promptYesOrNo

  # Define the base environment variables

  # Stage
  if JOINTS_STAGE not in environ or environ[JOINTS_STAGE] not in STAGES:
    environ[JOINTS_STAGE] = promptForAnswer('What stage is this system currently in', STAGES, PRODUCTION)

  # Architecture check
  isProduction = environ[JOINTS_STAGE] == PRODUCTION
  cpuCount = getCPUCount()

  # XXX: Important implementation note goes here
  #
  # This comment block has multiple lines
  # but it's a single paragraph
  #

  # Define the default environment variable values
  # Any environment variable with a defined value will not be prompted for later
  defaults = {}
"""

    with tempfile.NamedTemporaryFile(mode='w', suffix='.py', delete=False) as f:
      f.write(input_code)
      f.flush()

      changed = FileProcessor.processFile(Path(f.name), checkOnly=False)

      with open(f.name) as result_file:
        result = result_file.read()

      assert result == expected_code, f'Comment paragraph separation should be preserved\nGot:\n{result}'
      assert not changed, 'Input already correctly formatted - no changes needed'

  def testDecoratedClassDocstringAlwaysGetsBlankLine(self):
    """Regression: Decorated class docstrings should always have 1 blank line after them"""

    import tempfile
    from pathlib import Path
    from spacing.processor import FileProcessor

    # Set after_docstring = 0 to verify class docstrings are NOT affected
    config = BlankLineConfig.fromDefaults()
    config.afterDocstring = 0

    setConfig(config)

    input_code = '''@dataclass
class DICOMPushRequest:
  """Event payload representing a request to push a study"""

  source: 'PushSource'
  destination: 'AEConfiguration'
'''

    # Expected: Class docstrings ALWAYS get 1 blank line (PEP 257), regardless of after_docstring config
    expected_code = '''@dataclass
class DICOMPushRequest:
  """Event payload representing a request to push a study"""

  source: 'PushSource'
  destination: 'AEConfiguration'
'''

    with tempfile.NamedTemporaryFile(mode='w', suffix='.py', delete=False) as f:
      f.write(input_code)
      f.flush()

      changed = FileProcessor.processFile(Path(f.name), checkOnly=False)

      with open(f.name) as result_file:
        result = result_file.read()

      assert result == expected_code, f'Decorated class docstrings must have 1 blank line\nGot:\n{result}'
      assert not changed, 'Input already has correct formatting'

    # Reset config to defaults to avoid test pollution
    defaultConfig = BlankLineConfig.fromDefaults()

    setConfig(defaultConfig)

  def testConsecutiveControlBlocksGetBlankLine(self):
    """Regression: Consecutive if statements (control blocks) should have blank line between them"""

    import tempfile
    from pathlib import Path
    from spacing.processor import FileProcessor

    input_code = '''def makeDir(path):
  """Docstring"""
  if (not wasDir or forceGroup) and isDir:
    chgrp(path, groupname)

  if (not wasDir or forceMode) and isDir:
    chmod(path, mode)
'''

    # Expected: blank line after docstring added, blank line between consecutive control blocks preserved
    expected_code = '''def makeDir(path):
  """Docstring"""

  if (not wasDir or forceGroup) and isDir:
    chgrp(path, groupname)

  if (not wasDir or forceMode) and isDir:
    chmod(path, mode)
'''

    with tempfile.NamedTemporaryFile(mode='w', suffix='.py', delete=False) as f:
      f.write(input_code)
      f.flush()

      changed = FileProcessor.processFile(Path(f.name), checkOnly=False)

      with open(f.name) as result_file:
        result = result_file.read()

      assert result == expected_code, f'Consecutive if statements should keep blank line\nGot:\n{result}'

  def testPep8TwoBlankLinesBeforeCommentAtModuleLevel(self):
    """Regression: 2 blank lines before comment after module-level class definition"""

    input = [
      'class Foo:\n',
      '  pass\n',
      '\n',
      '# Comment before module-level variable\n',
      'x = 1\n',
    ]
    expected = [
      'class Foo:\n',
      '  pass\n',
      '\n',
      '\n',
      '# Comment before module-level variable\n',
      'x = 1\n',
    ]
    analyzer = FileAnalyzer()
    statements = analyzer.analyzeFile(input)
    ruleEngine = BlankLineRuleEngine()
    blankLineCounts = ruleEngine.applyRules(statements)
    result = FileProcessor._reconstructFile(statements, blankLineCounts, input)

    assert result == expected, f'Expected 2 blank lines before comment after class definition, got:\n{result}'

  def testPep8TwoBlankLinesBetweenDefinitionsWithComment(self):
    """Regression: 2 blank lines between top-level definitions even with comment in between"""

    input = [
      'def foo():\n',
      '  pass\n',
      '\n',
      '# Comment\n',
      'def bar():\n',
      '  pass\n',
    ]
    expected = [
      'def foo():\n',
      '  pass\n',
      '\n',
      '\n',
      '# Comment\n',
      'def bar():\n',
      '  pass\n',
    ]
    analyzer = FileAnalyzer()
    statements = analyzer.analyzeFile(input)
    ruleEngine = BlankLineRuleEngine()
    blankLineCounts = ruleEngine.applyRules(statements)
    result = FileProcessor._reconstructFile(statements, blankLineCounts, input)

    assert result == expected, f'Expected 2 blank lines before comment between definitions, got:\n{result}'
