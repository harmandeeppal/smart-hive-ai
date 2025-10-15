# Smart Hive AI - Professional Refactoring Plan

## Overview
This document outlines the professional restructuring of the Smart Hive AI codebase to follow industry best practices and Python PEP standards.

## New Directory Structure

```
smart-hive-ai/
├── src/
│   ├── __init__.py
│   ├── main.py (refactored app.py)
│   ├── config.py
│   ├── sensors/
│   │   ├── __init__.py
│   │   ├── mock_sensors.py (refactored mock_components.py)
│   │   └── real_sensors.py (refactored real_components.py)
│   └── utils/
│       ├── __init__.py
│       ├── timezone.py (refactored timezone_utils.py)
│       └── aws_client.py (AWS utilities)
├── dashboard/
│   ├── __init__.py
│   ├── app.py (refactored dashboard_app.py)
│   ├── static/
│   └── templates/
├── tests/
│   ├── __init__.py
│   ├── conftest.py (pytest configuration)
│   ├── test_sensors.py
│   ├── test_aws.py
│   ├── test_utils.py
│   └── fixtures/
├── scripts/
│   ├── check_dynamodb.py (refactored check_dynamodb_timestamps.py)
│   ├── update_dynamodb.py (refactored update_dynamodb_timestamps.py)
│   └── diagnose.py (refactored diagnose_dynamodb.py)
├── docs/
│   ├── README.md (Professional main documentation)
│   ├── api/
│   │   ├── sensors.md
│   │   ├── aws_integration.md
│   │   └── vision.md
│   ├── deployment/
│   │   ├── raspberry_pi.md
│   │   ├── docker.md
│   │   └── aws_setup.md
│   └── troubleshooting/
│       ├── hardware.md
│       ├── network.md
│       └── common_issues.md
├── models/
│   └── queen_bee.tflite
├── certs/
│   └── (AWS IoT certificates)
├── .github/
│   └── workflows/
│       └── ci.yml
├── requirements.txt
├── requirements-dev.txt
├── setup.py
├── pyproject.toml
├── .pylintrc
├── .flake8
├── .gitignore
├── LICENSE
├── CHANGELOG.md
├── CONTRIBUTING.md
└── CODE_OF_CONDUCT.md
```

## File Migrations

### Python Source Files
| Current Location | New Location | Status |
|---|---|---|
| app.py | src/main.py | To be refactored |
| config.py | src/config.py | To be refactored |
| mock_components.py | src/sensors/mock_sensors.py | To be refactored |
| real_components.py | src/sensors/real_sensors.py | To be refactored |
| timezone_utils.py | src/utils/timezone.py | To be refactored |
| dashboard/dashboard_app.py | dashboard/app.py | To be refactored |

### Scripts
| Current Location | New Location | Purpose |
|---|---|---|
| check_dynamodb_timestamps.py | scripts/check_dynamodb.py | DynamoDB verification |
| update_dynamodb_timestamps.py | scripts/update_dynamodb.py | Timestamp updates |
| diagnose_dynamodb.py | scripts/diagnose.py | Diagnostic tool |

### Documentation Consolidation
| Files to Merge | Target Location | Purpose |
|---|---|---|
| BME280_TROUBLESHOOTING.md<br>RASPBERRY_PI_ERROR_FIXES.md<br>DOCKER_FIXES.md | docs/troubleshooting/hardware.md | Hardware troubleshooting |
| DEPLOYMENT_GUIDE.md<br>DEPLOYMENT_ISSUES_AND_TFLITE.md | docs/deployment/raspberry_pi.md | Deployment guide |
| TIMEZONE_CONFIGURATION.md | docs/deployment/configuration.md | Configuration |
| SOUND_AI_INTEGRATION.md<br>CONTINUOUS_AI_VISION.md | docs/api/vision.md | AI/Vision API |
| TROUBLESHOOTING.md | docs/troubleshooting/common_issues.md | General troubleshooting |

### Files to Remove
- DOC_OVERVIEW.md (redundant - consolidated into main README)
- QUICK_REFERENCE.md (information moved to README)
- All .md files with emoji (to be rewritten professionally)

## Code Standards

### Python Module Headers (PEP 257)
```python
"""
Module name and description.

This module provides functionality for...

Classes:
    ClassName: Brief description

Functions:
    function_name: Brief description

Author:
    Harmandeep Pal

Created:
    October 2025

License:
    MIT License
"""
```

### Function/Method Documentation
```python
def function_name(param1: str, param2: int) -> bool:
    """
    Brief description of what the function does.
    
    This function performs... [detailed description if needed]
    
    Args:
        param1: Description of param1
        param2: Description of param2
    
    Returns:
        Description of return value
    
    Raises:
        ValueError: When condition occurs
        TypeError: When condition occurs
    
    Example:
        >>> function_name("test", 42)
        True
    """
```

### Class Documentation
```python
class ClassName:
    """
    Brief description of the class.
    
    This class handles... [detailed description]
    
    Attributes:
        attr1: Description of attribute
        attr2: Description of attribute
    
    Methods:
        method1: Brief description
        method2: Brief description
    
    Example:
        >>> obj = ClassName(param1, param2)
        >>> obj.method1()
    """
```

## Testing Strategy

### Test Structure
```python
"""
Test suite for module_name.

This test suite covers...

Test Classes:
    TestClassName: Tests for ClassName

Author:
    Harmandeep Pal

Created:
    October 2025
"""

import pytest
from src.module_name import ClassName

class TestClassName:
    """Test cases for ClassName."""
    
    def test_method_name(self):
        """Test that method_name behaves correctly."""
        # Arrange
        obj = ClassName()
        
        # Act
        result = obj.method_name()
        
        # Assert
        assert result == expected_value
```

## Implementation Phases

### Phase 1: Create New Structure (Current)
- [x] Create directory structure
- [ ] Move and refactor Python files
- [ ] Add professional headers to all files
- [ ] Remove emojis from all code

### Phase 2: Documentation
- [ ] Consolidate troubleshooting docs
- [ ] Create API documentation
- [ ] Rewrite README professionally
- [ ] Add CONTRIBUTING.md, CODE_OF_CONDUCT.md, CHANGELOG.md

### Phase 3: Testing Infrastructure
- [ ] Create test files
- [ ] Add pytest configuration
- [ ] Create test fixtures
- [ ] Add GitHub Actions CI/CD

### Phase 4: Code Quality
- [ ] Add .pylintrc configuration
- [ ] Add .flake8 configuration
- [ ] Add pyproject.toml for Black formatter
- [ ] Add pre-commit hooks

### Phase 5: Verification
- [ ] Run tests on laptop (mock environment)
- [ ] Run tests on Raspberry Pi (real hardware)
- [ ] Verify Docker containers work with new structure
- [ ] Update docker-compose.yml paths if needed

## Backward Compatibility

To ensure existing deployments continue working during transition:
1. Keep original files in place initially
2. Update import paths gradually
3. Test each component after migration
4. Update Dockerfile paths last
5. Create migration script for deployments

## Notes

- All emoji characters must be removed
- All print statements should use professional logging
- All docstrings must follow PEP 257
- Type hints should be added where possible
- Error handling should be comprehensive
