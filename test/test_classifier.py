"""
Tests for statement classifier.
Copyright (c) 2025-2026 Greg Smethells. All rights reserved.
See the accompanying AUTHORS file for a complete list of authors.
This file is subject to the terms and conditions defined in LICENSE.
"""

from spacing.classifier import StatementClassifier
from spacing.types import BlockType


class TestStatementClassifier:
  def testAssignmentClassification(self):
    # Variable assignment
    assert StatementClassifier.classifyStatement(['x = 1']) == BlockType.ASSIGNMENT
    assert StatementClassifier.classifyStatement(['result = func()']) == BlockType.ASSIGNMENT

    # Multiline assignment
    lines = ['result = complexFunction(', '  arg1,', '  arg2', ')']

    assert StatementClassifier.classifyStatement(lines) == BlockType.ASSIGNMENT

  def testCallClassification(self):
    assert StatementClassifier.classifyStatement(['func()']) == BlockType.CALL
    assert StatementClassifier.classifyStatement(['pass']) == BlockType.CALL
    assert StatementClassifier.classifyStatement(['assert x']) == BlockType.CALL
    assert StatementClassifier.classifyStatement(['raise ValueError()']) == BlockType.CALL

  def testFlowControlClassification(self):
    assert StatementClassifier.classifyStatement(['return x']) == BlockType.FLOW_CONTROL
    assert StatementClassifier.classifyStatement(['return']) == BlockType.FLOW_CONTROL
    assert StatementClassifier.classifyStatement(['yield item']) == BlockType.FLOW_CONTROL
    assert StatementClassifier.classifyStatement(['yield from generator()']) == BlockType.FLOW_CONTROL

  def testImportClassification(self):
    assert StatementClassifier.classifyStatement(['import sys']) == BlockType.IMPORT
    assert StatementClassifier.classifyStatement(['from os import path']) == BlockType.IMPORT

  def testControlClassification(self):
    assert StatementClassifier.classifyStatement(['if True:']) == BlockType.CONTROL
    assert StatementClassifier.classifyStatement(['for i in range(10):']) == BlockType.CONTROL
    assert StatementClassifier.classifyStatement(['try:']) == BlockType.CONTROL

  def testDefinitionClassification(self):
    assert StatementClassifier.classifyStatement(['def func():']) == BlockType.DEFINITION
    assert StatementClassifier.classifyStatement(['class MyClass:']) == BlockType.DEFINITION
    assert StatementClassifier.classifyStatement(['@decorator']) == BlockType.DEFINITION

  def testSecondaryClause(self):
    assert StatementClassifier.isSecondaryClause('elif condition:')
    assert StatementClassifier.isSecondaryClause('else:')
    assert StatementClassifier.isSecondaryClause('except Exception:')
    assert StatementClassifier.isSecondaryClause('finally:')
    assert not StatementClassifier.isSecondaryClause('if condition:')


class TestClassifierRegressions:
  """Regression tests for classifier bugs"""

  def testAsyncDefClassifiedAsDefinition(self):
    """Regression: async def should be DEFINITION, not CALL"""

    asyncDefLine = ['  async def method(self):']
    blockType = StatementClassifier.classifyStatement(asyncDefLine)

    assert blockType == BlockType.DEFINITION, f'async def should be DEFINITION, got {blockType.name}'

    # Test regular def for comparison
    defLine = ['  def method(self):']
    blockType = StatementClassifier.classifyStatement(defLine)

    assert blockType == BlockType.DEFINITION

  def testDictionaryAssignmentWithStringKeyClassification(self):
    """Regression: environ['STRING_KEY'] = value was misclassified as CALL instead of ASSIGNMENT"""

    # Test dictionary assignment with string literal key
    line1 = ["  environ['JOINTS_TEST_SUITE'] = 'True'"]
    blockType1 = StatementClassifier.classifyStatement(line1)

    assert blockType1 == BlockType.ASSIGNMENT, f"environ['STRING'] = value should be ASSIGNMENT, got {blockType1.name}"

    # Test dictionary assignment with constant key
    line2 = ["  environ[CONSTANT_KEY] = 'False'"]
    blockType2 = StatementClassifier.classifyStatement(line2)

    assert blockType2 == BlockType.ASSIGNMENT, f'environ[CONSTANT] = value should be ASSIGNMENT, got {blockType2.name}'

    # Test with attribute access in key
    line3 = ["  environ[Secret.KEY] = 'value'"]
    blockType3 = StatementClassifier.classifyStatement(line3)

    assert blockType3 == BlockType.ASSIGNMENT, f'environ[obj.attr] = value should be ASSIGNMENT, got {blockType3.name}'

  def testIfStatementWithParenthesesClassifiedAsControl(self):
    """Regression: if statements with parentheses should be CONTROL, not CALL"""

    # Test various if statement formats
    lines1 = ['  if (IS_LINUX) and path and username:']
    blockType1 = StatementClassifier.classifyStatement(lines1)

    assert blockType1 == BlockType.CONTROL, f'if (complex) should be CONTROL, got {blockType1.name}'

    lines2 = ['  if (not wasDir or forceMode) and isDir:']
    blockType2 = StatementClassifier.classifyStatement(lines2)

    assert blockType2 == BlockType.CONTROL, f'if (complex boolean) should be CONTROL, got {blockType2.name}'

    lines3 = ['  while (x > 0) and (y < 10):']
    blockType3 = StatementClassifier.classifyStatement(lines3)

    assert blockType3 == BlockType.CONTROL, f'while (complex) should be CONTROL, got {blockType3.name}'

  def testReturnAndYieldClassifiedAsFlowControl(self):
    """Regression: return and yield should be FLOW_CONTROL, not CALL"""

    # Test return statements
    assert StatementClassifier.classifyStatement(['return result']) == BlockType.FLOW_CONTROL
    assert StatementClassifier.classifyStatement(['return']) == BlockType.FLOW_CONTROL

    # Test yield statements
    assert StatementClassifier.classifyStatement(['yield item']) == BlockType.FLOW_CONTROL
    assert StatementClassifier.classifyStatement(['yield from generator()']) == BlockType.FLOW_CONTROL

    # Test that other keywords remain CALL
    assert StatementClassifier.classifyStatement(['assert condition']) == BlockType.CALL
    assert StatementClassifier.classifyStatement(['raise ValueError()']) == BlockType.CALL
    assert StatementClassifier.classifyStatement(['pass']) == BlockType.CALL
    assert StatementClassifier.classifyStatement(['del item']) == BlockType.CALL

  def testControlStatementWithEqualsInStringLiteral(self):
    """Regression: if 'CN=' in subject was misclassified as ASSIGNMENT due to equals in string"""

    # Control statement with equals sign in string literal
    assert StatementClassifier.classifyStatement(["if subject is not None and 'CN=' in subject:"]) == BlockType.CONTROL

    # Control statement with equals in various string formats
    assert StatementClassifier.classifyStatement(['if "key=value" in text:']) == BlockType.CONTROL
    assert StatementClassifier.classifyStatement(["if 'x=5' in data:"]) == BlockType.CONTROL

  def testYieldWithParenthesesClassifiedAsFlowControl(self):
    """Regression: yield (Status.SUCCESS, None) was misclassified as CALL instead of FLOW_CONTROL"""

    # yield with parentheses (tuple syntax)
    assert StatementClassifier.classifyStatement(['yield (Status.SUCCESS, None)']) == BlockType.FLOW_CONTROL

    # yield with function call result
    assert StatementClassifier.classifyStatement(['yield getData()']) == BlockType.FLOW_CONTROL

    # return with parentheses
    assert StatementClassifier.classifyStatement(['return (x, y)']) == BlockType.FLOW_CONTROL

  def testFStringInDictionaryAssignmentClassifiedAsAssignment(self):
    """Regression: cookies[f'{VAR}_0'] = value was misclassified as CALL instead of ASSIGNMENT"""

    # F-string as dictionary key
    assert StatementClassifier.classifyStatement(["cookies[f'{CERTIFICATE}_0'] = '\"junk\"'"]) == BlockType.ASSIGNMENT

    # F-string with multiple variables
    assert StatementClassifier.classifyStatement(["data[f'{prefix}_{suffix}'] = value"]) == BlockType.ASSIGNMENT

    # Regular dictionary assignment (no f-string) for comparison
    assert StatementClassifier.classifyStatement(['cookies[SIGNATURE] = \'"junk"\'']) == BlockType.ASSIGNMENT

  def testDictionaryAssignmentWithMethodCallInKey(self):
    """Regression: dict[methodCall()] = value was misclassified as CALL instead of ASSIGNMENT"""

    # Method call in dictionary key
    assert (
      StatementClassifier.classifyStatement(['ctx.request.cookies[getApprovalCookieName()] = str(approval)'])
      == BlockType.ASSIGNMENT
    )

    # Method call with arguments in dictionary key
    assert (
      StatementClassifier.classifyStatement(['ctx.request.cookies[getTwoFactorAuthCookieName()] = str(twoFactorAuth)'])
      == BlockType.ASSIGNMENT
    )

    # Method call in both key and value
    assert StatementClassifier.classifyStatement(['data[getKey()] = getValue()']) == BlockType.ASSIGNMENT

  def testDictionaryAssignmentWithHyphensInStringKey(self):
    """Regression: dict['key-with-hyphens'] = value was misclassified as CALL instead of ASSIGNMENT"""

    # String key with hyphens (HTTP headers)
    assert (
      StatementClassifier.classifyStatement(["response.headers['Access-Control-Allow-Origin'] = allowedOrigin"])
      == BlockType.ASSIGNMENT
    )

    # Multiple hyphens in string
    assert (
      StatementClassifier.classifyStatement(["response.headers['Access-Control-Allow-Headers'] = 'X-JOINTS-CLIENT-ID'"])
      == BlockType.ASSIGNMENT
    )

    # Hyphen at start or end of string
    assert StatementClassifier.classifyStatement(["data['-key-'] = value"]) == BlockType.ASSIGNMENT

  def testDictionaryAssignmentWithSpecialCharactersInStringKey(self):
    """Test that assignments with various special characters in string keys are classified as ASSIGNMENT"""

    # Colon (URLs, timestamps)
    assert (
      StatementClassifier.classifyStatement(["cache['http://example.com:8080/path'] = data"]) == BlockType.ASSIGNMENT
    )

    assert StatementClassifier.classifyStatement(["events['2025-11-09:14:30:00'] = event"]) == BlockType.ASSIGNMENT

    # Slash (paths, URLs)
    assert StatementClassifier.classifyStatement(["routes['/api/v1/users'] = handler"]) == BlockType.ASSIGNMENT
    assert StatementClassifier.classifyStatement(["paths['src/spacing/config.py'] = config"]) == BlockType.ASSIGNMENT

    # Plus (URLs, versions)
    assert StatementClassifier.classifyStatement(["params['name+space'] = value"]) == BlockType.ASSIGNMENT
    assert StatementClassifier.classifyStatement(["versions['v1.0+build.123'] = release"]) == BlockType.ASSIGNMENT

    # Ampersand (URLs)
    assert StatementClassifier.classifyStatement(["queries['?user=john&age=30'] = result"]) == BlockType.ASSIGNMENT

    # Question mark (URLs)
    assert (
      StatementClassifier.classifyStatement(["urls['http://example.com?query'] = response"]) == BlockType.ASSIGNMENT
    )

    # Semicolon (data formats)
    assert StatementClassifier.classifyStatement(["data['field1;field2;field3'] = values"]) == BlockType.ASSIGNMENT

    # At sign (emails)
    assert StatementClassifier.classifyStatement(["users['user@example.com'] = profile"]) == BlockType.ASSIGNMENT

    # Hash/pound (fragments, IDs)
    assert (
      StatementClassifier.classifyStatement(["urls['http://example.com#section'] = anchor"]) == BlockType.ASSIGNMENT
    )

    assert StatementClassifier.classifyStatement(["ids['#user-123'] = userId"]) == BlockType.ASSIGNMENT

    # Percent (URL encoding)
    assert StatementClassifier.classifyStatement(["encoded['hello%20world'] = decoded"]) == BlockType.ASSIGNMENT

    # Asterisk (wildcards)
    assert StatementClassifier.classifyStatement(["patterns['*.py'] = files"]) == BlockType.ASSIGNMENT

    # Pipe (delimiters)
    assert StatementClassifier.classifyStatement(["data['field1|field2|field3'] = record"]) == BlockType.ASSIGNMENT

    # Multiple special characters combined
    assert (
      StatementClassifier.classifyStatement(
        ["cache['https://api.example.com:443/v1/users?id=123&name=john#top'] = response"]
      )
      == BlockType.ASSIGNMENT
    )

  def testComparisonOperatorsNotMisclassifiedAsAssignment(self):
    """Ensure comparison operators (!=, <=, >=) are NOT classified as ASSIGNMENT"""

    # These should NOT be ASSIGNMENT (they're comparison expressions, likely CALL as default)
    assert StatementClassifier.classifyStatement(['if x != y:']) == BlockType.CONTROL
    assert StatementClassifier.classifyStatement(['if x <= y:']) == BlockType.CONTROL
    assert StatementClassifier.classifyStatement(['if x >= y:']) == BlockType.CONTROL

    # Standalone comparisons (not in control statements)
    assert (
      StatementClassifier.classifyStatement(['result = (x != y)']) == BlockType.ASSIGNMENT
    )  # Assignment of comparison result
    assert StatementClassifier.classifyStatement(['x != y']) != BlockType.ASSIGNMENT  # Just comparison, should be CALL

  def testMethodCallsWithLambdaKeywordArgumentsClassifiedAsCall(self):
    """Regression: method calls with lambda keyword arguments should be CALL, not ASSIGNMENT"""

    # Lambda in keyword argument
    assert StatementClassifier.classifyStatement(['output[STUDY].sort(key=lambda k: k[SDATE])']) == BlockType.CALL

    # Multiple method calls with lambdas
    assert StatementClassifier.classifyStatement(['output[PATIENT].sort(key=lambda k: k[PNAME])']) == BlockType.CALL

    # Lambda with more complex expression
    assert (
      StatementClassifier.classifyStatement(['items.filter(predicate=lambda x: x.isValid and x.count > 0)'])
      == BlockType.CALL
    )

  def testAsyncWithAndAsyncForClassifiedAsControl(self):
    """Regression: async with and async for should be CONTROL, not CALL"""

    # async with
    assert StatementClassifier.classifyStatement(['async with self.lock:']) == BlockType.CONTROL
    assert StatementClassifier.classifyStatement(['  async with websocketsLock:']) == BlockType.CONTROL

    # async for
    assert StatementClassifier.classifyStatement(['async for item in queue:']) == BlockType.CONTROL
    assert StatementClassifier.classifyStatement(['  async for msg in stream:']) == BlockType.CONTROL

    # Regular with/for should still work
    assert StatementClassifier.classifyStatement(['with open(file):']) == BlockType.CONTROL
    assert StatementClassifier.classifyStatement(['for i in range(10):']) == BlockType.CONTROL
