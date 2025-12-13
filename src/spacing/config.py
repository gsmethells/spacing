"""
Configuration management for spacing blank line rules.
Copyright (c) 2025-2026 Greg Smethells. All rights reserved.
See the accompanying AUTHORS file for a complete list of authors.
This file is subject to the terms and conditions defined in LICENSE.
"""

import tomllib
from .types import BlockType
from dataclasses import dataclass, field

# Maximum number of blank lines allowed in configuration
# Rationale: More than 3 blank lines is excessive and likely unintentional.
# PEP 8 recommends maximum of 2 blank lines, we allow 3 for flexibility.
MAX_BLANK_LINES = 3

# Valid range for indent width (spaces per tab character)
# Rationale: Standard Python indentation is 2, 4, or 8 spaces.
# We allow 1-8 for flexibility while preventing unreasonable values.
MIN_INDENT_WIDTH = 1
MAX_INDENT_WIDTH = 8


@dataclass
class BlankLineConfig:
  """Configuration for blank line rules between block types"""

  defaultBetweenDifferent: int = 1
  transitions: dict = field(default_factory=dict)
  consecutiveControl: int = 1
  consecutiveDefinition: int = 1
  afterDocstring: int = 1
  indentWidth: int = 2
  excludeNames: list = field(default_factory=list)
  excludePatterns: list = field(default_factory=list)
  includeHidden: bool = False

  @classmethod
  def fromToml(cls, configPath):
    """Load configuration from TOML file
    :param configPath: Path to spacing.toml file
    :type configPath: Path
    :rtype: BlankLineConfig
    :raises: ValueError for invalid configuration values
    :raises: FileNotFoundError if config file doesn't exist
    """

    if not configPath.exists():
      raise FileNotFoundError(f'Configuration file not found: {configPath}')

    try:
      with open(configPath, 'rb') as f:
        data = tomllib.load(f)
    except tomllib.TOMLDecodeError as e:
      raise ValueError(f'Failed to parse TOML file {configPath}: {e}')
    except OSError as e:
      raise ValueError(f'Failed to read TOML file {configPath}: {e}')

    # Validate top-level sections
    validSections = {'blank_lines', 'paths'}
    unknownSections = set(data.keys()) - validSections

    if unknownSections:
      raise ValueError(
        f'Unknown configuration sections: {", ".join(sorted(unknownSections))}. Valid sections: {", ".join(sorted(validSections))}'
      )

    blankLinesConfig = data.get('blank_lines', {})
    pathsConfig = data.get('paths', {})

    # Parse default value
    defaultBetweenDifferent = blankLinesConfig.get('default_between_different', 1)

    cls._validateBlankLineCount(defaultBetweenDifferent, 'default_between_different')

    # Parse special rules
    consecutiveControl = blankLinesConfig.get('consecutive_control', 1)
    consecutiveDefinition = blankLinesConfig.get('consecutive_definition', 1)
    afterDocstring = blankLinesConfig.get('after_docstring', 1)

    cls._validateBlankLineCount(consecutiveControl, 'consecutive_control')
    cls._validateBlankLineCount(consecutiveDefinition, 'consecutive_definition')
    cls._validateBlankLineCount(afterDocstring, 'after_docstring')

    # Parse indent width
    indentWidth = blankLinesConfig.get('indent_width', 2)

    cls._validateIndentWidth(indentWidth, 'indent_width')

    # Parse transition overrides
    transitions = {}
    validBlankLinesKeys = {
      'default_between_different',
      'consecutive_control',
      'consecutive_definition',
      'after_docstring',
      'indent_width',
    }

    for key, value in blankLinesConfig.items():
      if key in validBlankLinesKeys:
        continue

      # Validate this is a properly formatted transition key
      # Parse transition key (e.g., "assignment_to_call")
      parts = key.split('_to_')

      if len(parts) != 2:
        raise ValueError(f'Invalid transition key format: {key}. Expected format: blocktype_to_blocktype')

      fromBlockName, toBlockName = parts

      try:
        fromBlock = cls._parseBlockType(fromBlockName)
        toBlock = cls._parseBlockType(toBlockName)
      except ValueError as e:
        raise ValueError(f'Invalid transition key {key}: {e}')

      cls._validateBlankLineCount(value, key)

      transitions[(fromBlock, toBlock)] = value

    # Parse path exclusions
    excludeNames = pathsConfig.get('exclude_names', [])
    excludePatterns = pathsConfig.get('exclude_patterns', [])
    includeHidden = pathsConfig.get('include_hidden', False)

    if not isinstance(excludeNames, list):
      raise ValueError('paths.exclude_names must be a list')

    if not isinstance(excludePatterns, list):
      raise ValueError('paths.exclude_patterns must be a list')

    if not isinstance(includeHidden, bool):
      raise ValueError('paths.include_hidden must be a boolean')

    return cls(
      defaultBetweenDifferent=defaultBetweenDifferent,
      transitions=transitions,
      consecutiveControl=consecutiveControl,
      consecutiveDefinition=consecutiveDefinition,
      afterDocstring=afterDocstring,
      indentWidth=indentWidth,
      excludeNames=excludeNames,
      excludePatterns=excludePatterns,
      includeHidden=includeHidden,
    )

  @classmethod
  def fromDefaults(cls) -> 'BlankLineConfig':
    """Create configuration with default values (current behavior)
    :rtype: BlankLineConfig
    """

    return cls()

  def getBlankLines(self, fromBlock, toBlock, indentLevel=None, isClassDocstring=False, isModuleLevelDocstring=False):
    """Get number of blank lines for transition between block types
    :param fromBlock: Source block type
    :type fromBlock: BlockType
    :param toBlock: Target block type
    :type toBlock: BlockType
    :param indentLevel: Indentation level for scope-aware rules (None = unknown)
    :type indentLevel: int
    :param isClassDocstring: True if fromBlock is a class docstring (not configurable)
    :type isClassDocstring: bool
    :param isModuleLevelDocstring: True if fromBlock is a module-level docstring (not configurable)
    :type isModuleLevelDocstring: bool
    :rtype: int
    """

    # Check for specific transition override first
    key = (fromBlock, toBlock)

    if key in self.transitions:
      blankLines = self.transitions[key]
    elif fromBlock == toBlock:
      # Handle same-type special rules
      if fromBlock == BlockType.CONTROL:
        blankLines = self.consecutiveControl
      elif fromBlock == BlockType.DEFINITION:
        # PEP 8: 2 blank lines at module level (indent 0), 1 blank line nested
        if indentLevel == 0:
          blankLines = 2
        else:
          blankLines = self.consecutiveDefinition
      else:
        # Same type blocks (except Control/Definition) have no blank lines
        blankLines = 0
    else:
      # PEP 8: Surround top-level function and class definitions with 2 blank lines
      # This takes precedence over docstring rules when transitioning to a definition
      if indentLevel == 0 and toBlock == BlockType.DEFINITION:
        blankLines = 2

      # PEP 8: 2 blank lines FROM module-level definitions
      elif indentLevel == 0 and fromBlock == BlockType.DEFINITION:
        blankLines = 2

      # PEP 257: blank line after docstrings
      # Module-level and class docstrings ALWAYS get 1 blank line (non-configurable)
      # Method/function docstrings use afterDocstring config (default 1)
      elif fromBlock == BlockType.DOCSTRING and toBlock != BlockType.DOCSTRING:
        if isClassDocstring or isModuleLevelDocstring:
          blankLines = 1  # Always 1 for class and module-level docstrings
        else:
          blankLines = self.afterDocstring  # Configurable for method/function docstrings
      else:
        # Use default for different block types
        blankLines = self.defaultBetweenDifferent

    return blankLines

  @staticmethod
  def _parseBlockType(blockTypeName: str) -> BlockType:
    """Parse block type name from string
    :param blockTypeName: Name of block type (e.g., 'assignment', 'call')
    :type blockTypeName: str
    :rtype: BlockType
    :raises: ValueError if block type name is invalid
    """

    blockTypeMap = {
      'assignment': BlockType.ASSIGNMENT,
      'call': BlockType.CALL,
      'import': BlockType.IMPORT,
      'control': BlockType.CONTROL,
      'definition': BlockType.DEFINITION,
      'declaration': BlockType.DECLARATION,
      'docstring': BlockType.DOCSTRING,
      'comment': BlockType.COMMENT,
      'type_annotation': BlockType.TYPE_ANNOTATION,
      'annotation': BlockType.TYPE_ANNOTATION,  # Allow shorter alias
    }

    if blockTypeName not in blockTypeMap:
      validNames = ', '.join(blockTypeMap.keys())

      raise ValueError(f'Unknown block type: {blockTypeName}. Valid types: {validNames}')

    return blockTypeMap[blockTypeName]

  @staticmethod
  def _validateBlankLineCount(value: int, key: str):
    """Validate blank line count is in valid range (0-MAX_BLANK_LINES)
    :param value: Blank line count to validate
    :type value: int
    :param key: Configuration key name for error messages
    :type key: str
    :raises: ValueError if value is invalid
    """

    if not isinstance(value, int):
      raise ValueError(f'{key} must be an integer, got {type(value).__name__}: {value}')

    if value < 0 or value > MAX_BLANK_LINES:
      raise ValueError(f'{key} must be between 0 and {MAX_BLANK_LINES}, got: {value}')

  @staticmethod
  def _validateIndentWidth(value: int, key: str):
    """Validate indent width is in valid range (MIN_INDENT_WIDTH-MAX_INDENT_WIDTH)
    :param value: Indent width to validate (spaces per tab)
    :type value: int
    :param key: Configuration key name for error messages
    :type key: str
    :raises: ValueError if value is invalid
    """

    if not isinstance(value, int):
      raise ValueError(f'{key} must be an integer, got {type(value).__name__}: {value}')

    if value < MIN_INDENT_WIDTH or value > MAX_INDENT_WIDTH:
      raise ValueError(f'{key} must be between {MIN_INDENT_WIDTH} and {MAX_INDENT_WIDTH}, got: {value}')


# Global configuration instance available for import
config = BlankLineConfig.fromDefaults()


def setConfig(newConfig):
  """Update the global configuration instance
  :param newConfig: Configuration to set as global
  :type newConfig: BlankLineConfig
  """

  global config

  config = newConfig
