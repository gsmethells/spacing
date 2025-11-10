"""
Test class method transitions.
Copyright (c) 2025-2026 Greg Smethells. All rights reserved.
See the accompanying AUTHORS file for a complete list of authors.
This file is subject to the terms and conditions defined in LICENSE.
"""

import tempfile
from pathlib import Path
from spacing.processor import FileProcessor


class TestClassMethods:
  def testBlankLineBetweenClassMethods(self):
    """Test that blank line is added between ASSIGNMENT and CALL in method bodies"""

    input_code = """class MyClass:
  def method1(self):
    x = 1
    return x

  def method2(self):
    y = 2
    return y
"""
    expected_code = """class MyClass:
  def method1(self):
    x = 1

    return x

  def method2(self):
    y = 2

    return y
"""

    with tempfile.NamedTemporaryFile(mode='w', suffix='.py', delete=False) as f:
      f.write(input_code)
      f.flush()

      changed = FileProcessor.processFile(Path(f.name), checkOnly=False)

      # Should add blank lines between ASSIGNMENT and CALL
      assert changed

      with open(f.name) as result_file:
        result = result_file.read()

      assert result == expected_code

  def testBlankLineAfterMethodBody(self):
    """Test that blank line is added between ASSIGNMENT and CALL in method body"""

    input_code = '''class AIService:
  def __init__(self):
    self.aiAvailable = False
    logger.warning('AIService initialized without AI support - Vertex AI not available')

    # Rate limiting state
    self.last_request_time = 0
    self.min_request_interval = 1.0  # Minimum 1 second between requests

  def _call(self, prompt, operation_name):
    """Call the AI model"""
    pass
'''
    expected_code = '''class AIService:
  def __init__(self):
    self.aiAvailable = False

    logger.warning('AIService initialized without AI support - Vertex AI not available')

    # Rate limiting state
    self.last_request_time = 0
    self.min_request_interval = 1.0  # Minimum 1 second between requests

  def _call(self, prompt, operation_name):
    """Call the AI model"""

    pass
'''

    with tempfile.NamedTemporaryFile(mode='w', suffix='.py', delete=False) as f:
      f.write(input_code)
      f.flush()

      changed = FileProcessor.processFile(Path(f.name), checkOnly=False)

      # Should add blank line between ASSIGNMENT and CALL
      assert changed

      with open(f.name) as result_file:
        result = result_file.read()

      assert result == expected_code

  def testNestedFunctionInMethod(self):
    """Test that nested functions within methods follow function body rules"""

    input_code = """class MyClass:
  def outer_method(self):
    x = 1
    
    def inner_function():
      return x * 2
    
    return inner_function()
"""
    expected_output = """class MyClass:
  def outer_method(self):
    x = 1

    def inner_function():
      return x * 2

    return inner_function()
"""

    with tempfile.NamedTemporaryFile(mode='w', suffix='.py', delete=False) as f:
      f.write(input_code)
      f.flush()

      changed = FileProcessor.processFile(Path(f.name), checkOnly=False)

      with open(f.name) as result_file:
        result = result_file.read()

      # Nested functions should follow function body rules
      assert result == expected_output

  def testClassWithMultipleMethods(self):
    """Test class with multiple methods adds blank lines between ASSIGNMENT and CALL"""

    input_code = """class Calculator:
  def __init__(self):
    self.result = 0

  def add(self, x):
    self.result += x
    return self.result

  def subtract(self, x):
    self.result -= x
    return self.result

  def reset(self):
    self.result = 0
"""
    expected_code = """class Calculator:
  def __init__(self):
    self.result = 0

  def add(self, x):
    self.result += x

    return self.result

  def subtract(self, x):
    self.result -= x

    return self.result

  def reset(self):
    self.result = 0
"""

    with tempfile.NamedTemporaryFile(mode='w', suffix='.py', delete=False) as f:
      f.write(input_code)
      f.flush()

      changed = FileProcessor.processFile(Path(f.name), checkOnly=False)

      # Should add blank lines between ASSIGNMENT and CALL in add() and subtract()
      assert changed

      with open(f.name) as result_file:
        result = result_file.read()

      assert result == expected_code

  def testClassAttributesAndMethods(self):
    """Test that class attributes and methods have proper spacing"""

    input_code = """class Config:
  # Class attributes
  DEBUG = True
  VERSION = "1.0"

  def __init__(self):
    self.settings = {}

  def load(self):
    pass
"""

    with tempfile.NamedTemporaryFile(mode='w', suffix='.py', delete=False) as f:
      f.write(input_code)
      f.flush()

      changed = FileProcessor.processFile(Path(f.name), checkOnly=False)

      # Should not change
      assert not changed

      with open(f.name) as result_file:
        result = result_file.read()

      assert result == input_code

  def testClassMethodBlankLineRegression(self):
    """Regression test: ensure blank lines between consecutive class methods are preserved"""

    input_code = """class Service:
  def method1(self):
    pass

  def method2(self):
    pass

  def method3(self):
    pass
"""

    with tempfile.NamedTemporaryFile(mode='w', suffix='.py', delete=False) as f:
      f.write(input_code)
      f.flush()

      changed = FileProcessor.processFile(Path(f.name), checkOnly=False)

      # Should not change - blank lines between methods should be preserved
      assert not changed

      with open(f.name) as result_file:
        result = result_file.read()

      assert result == input_code

  def testClassWithMixedMembersRegression(self):
    """Regression test: ensure blank lines are preserved between different member types"""

    input_code = """class Complex:
  # Class comment
  VALUE = 42

  def __init__(self):
    self.data = []

  @property
  def size(self):
    return len(self.data)

  def process(self):
    return self.VALUE
"""

    with tempfile.NamedTemporaryFile(mode='w', suffix='.py', delete=False) as f:
      f.write(input_code)
      f.flush()

      changed = FileProcessor.processFile(Path(f.name), checkOnly=False)

      # Should not change - proper spacing already exists
      assert not changed

      with open(f.name) as result_file:
        result = result_file.read()

      assert result == input_code
