# Smart Hive AI - Professional Refactoring Action Plan

## Status: Foundation Complete - Ready for Migration

Your Smart Hive AI project now has a professional foundation. Here's what to do next.

---

## What Has Been Done

### 1. Professional Infrastructure Created
- Directory structure (src/, tests/, scripts/, docs/)
- Professional main module (src/main.py) with:
  - Comprehensive docstrings (PEP 257)
  - Type hints (PEP 484)
  - Professional logging (no emojis)
  - Proper error handling
  - Author and license information
- Test infrastructure (pytest with fixtures)
- Code quality configs (.pylintrc, .flake8, pyproject.toml)
- Migration automation script
- Comprehensive documentation

### 2. Files Committed to GitHub
- src/main.py
- migrate_to_professional_structure.py
- REFACTORING_PLAN.md
- PROFESSIONAL_REFACTORING_SUMMARY.md
- Directory structure (empty folders committed)

---

## Your Next Steps

### Step 1: Review the Foundation (15 minutes)

Read these documents in order:
1. **PROFESSIONAL_REFACTORING_SUMMARY.md** - Overview of changes
2. **REFACTORING_PLAN.md** - Detailed implementation plan
3. **src/main.py** - Example of professional code

Questions to answer:
- Do you understand the new structure?
- Are you comfortable with the docstring format?
- Do you want any changes to the organization?

### Step 2: Run Migration (Dry-Run First) (10 minutes)

```bash
# See what will be done (no changes made)
python migrate_to_professional_structure.py --dry-run --verbose

# Review the output carefully
# If everything looks good, proceed to Step 3
```

### Step 3: Execute Migration (5 minutes)

```bash
# Execute the migration
python migrate_to_professional_structure.py --verbose

# Check what changed
git status
git diff

# Review the changes
```

### Step 4: Manual Refactoring (2-3 hours)

The migration script creates the foundation. You still need to manually:

#### A. Refactor Remaining Python Files

**mock_components.py → src/sensors/mock_sensors.py:**
```python
"""
Mock sensor implementations for development and testing.

This module provides simulated sensor classes that mimic real hardware behavior
without requiring physical sensors. Used in development and testing environments.

Classes:
    MockBME280: Simulated temperature/humidity sensor
    MockLIS3DH: Simulated vibration sensor
    MockINMP441: Simulated sound sensor
    MockVisionProcessor: Simulated computer vision processor

Author:
    Harmandeep Pal

Created:
    October 2025

License:
    MIT License
"""

import random
import time
from typing import Tuple

# Remove all emojis
# Add type hints
# Add comprehensive docstrings
# Follow the pattern in src/main.py
```

**real_components.py → src/sensors/real_sensors.py:**
```python
"""
Real hardware sensor implementations.

This module provides interfaces to physical sensors on the Raspberry Pi including
BME280 (temperature/humidity), LIS3DH (vibration), INMP441 (sound), and camera
with AI vision processing.

Classes:
    RealBME280: BME280 temperature/humidity sensor interface
    RealLIS3DH: LIS3DH accelerometer interface
    RealINMP441: INMP441 microphone interface
    RealVisionProcessor: Computer vision with TensorFlow Lite

Author:
    Harmandeep Pal

Created:
    October 2025

License:
    MIT License
"""

# Remove all emojis
# Add type hints
# Add comprehensive docstrings
# Use logging instead of print
```

**timezone_utils.py → src/utils/timezone.py:**
```python
"""
Timezone utility functions for New Zealand localization.

Provides timezone conversion utilities for displaying timestamps in
New Zealand timezone (Pacific/Auckland) with proper daylight saving handling.

Functions:
    convert_to_nz_time: Convert Unix timestamp to NZ datetime
    format_nz_timestamp: Format timestamp as NZ timezone string

Author:
    Harmandeep Pal

Created:
    October 2025

License:
    MIT License
"""

# Add professional docstrings
# Add type hints
# Remove emojis
```

**config.py → src/config.py:**
```python
"""
Smart Hive AI Configuration Module.

Central configuration for all system parameters including AWS credentials,
sensor settings, and operational parameters.

Constants:
    IS_MOCK_ENVIRONMENT: Development/production mode toggle
    AWS_ENDPOINT: AWS IoT Core endpoint
    ENABLE_DYNAMODB: DynamoDB persistence toggle
    TELEMETRY_INTERVAL_SECONDS: Sensor reading interval

Author:
    Harmandeep Pal

Created:
    October 2025

License:
    MIT License
"""

# Add comprehensive module docstring
# Group related constants with comments
# No emojis in comments
```

#### B. Refactor Scripts

**check_dynamodb_timestamps.py → scripts/check_dynamodb.py:**
```python
"""
DynamoDB telemetry verification script.

Queries the DynamoDB table to verify data persistence and display recent
telemetry records with New Zealand timestamps.

Functions:
    main: Entry point for verification

Author:
    Harmandeep Pal

Usage:
    python scripts/check_dynamodb.py
"""

# Add professional header
# Use logging instead of print
# Add type hints
```

**update_dynamodb_timestamps.py → scripts/update_dynamodb.py:**
```python
"""
DynamoDB timestamp update utility.

Updates existing DynamoDB records with New Zealand timezone fields
for improved human readability in AWS Console.

Functions:
    main: Entry point for update process

Author:
    Harmandeep Pal

Usage:
    python scripts/update_dynamodb.py
"""
```

**diagnose_dynamodb.py → scripts/diagnose.py:**
```python
"""
DynamoDB diagnostic tool.

Comprehensive diagnostic script for troubleshooting DynamoDB connectivity,
permissions, and data flow issues.

Functions:
    main: Entry point for diagnostics

Author:
    Harmandeep Pal

Usage:
    python scripts/diagnose.py
"""
```

#### C. Refactor Dashboard

**dashboard/dashboard_app.py → dashboard/app.py:**
```python
"""
Smart Hive AI Dashboard Application.

Web-based dashboard for real-time monitoring and control of the Smart Hive
system. Provides live telemetry visualization, video streaming, and sensor
control capabilities.

Classes:
    DashboardServer: Flask application server

Functions:
    main: Entry point for dashboard

Author:
    Harmandeep Pal

Created:
    October 2025

License:
    MIT License
"""

# Add professional header
# Use logging instead of print
# Remove emojis from HTML templates
# Add docstrings to all functions
```

### Step 5: Update Import Paths

After moving files, update all imports:

**In Dockerfile.edge:**
```dockerfile
# Change:
CMD ["python", "app.py"]

# To:
CMD ["python", "-m", "src.main"]
```

**In docker-compose.yml:**
```yaml
# Verify volume mounts still work
# No changes needed if using WORKDIR /app
```

**In all Python files:**
```python
# Change:
import config
from mock_components import MockBME280
from real_components import RealBME280

# To:
from src import config
from src.sensors.mock_sensors import MockBME280
from src.sensors.real_sensors import RealBME280
```

### Step 6: Create Missing Documentation (1-2 hours)

#### A. Professional README.md (No Emojis)

```markdown
# Smart Hive AI

Production-ready IoT and Edge AI system for intelligent honeybee colony monitoring.

## Overview

Smart Hive AI combines environmental sensors, computer vision, and AWS cloud
services to enable real-time monitoring of bee hive health with AI-powered
queen detection.

## Features

- Real-time environmental monitoring (temperature, humidity, vibration, sound)
- AI-powered queen bee detection using YOLOv5 TensorFlow Lite
- Live video streaming with detection overlays
- AWS cloud integration (IoT Core, DynamoDB, S3)
- Interactive web dashboard
- Fully containerized deployment

## Architecture

[Include architecture diagram without emojis]

## Installation

[Professional installation instructions]

## Usage

[Clear usage instructions]

## Development

[Development setup guide]

## Testing

```bash
pytest tests/ -v --cov=src
```

## Contributing

See CONTRIBUTING.md for guidelines.

## License

MIT License - see LICENSE file.

## Author

Harmandeep Pal
Auckland University of Technology
```

#### B. CONTRIBUTING.md

```markdown
# Contributing to Smart Hive AI

Thank you for your interest in contributing...

## Code Standards

- Follow PEP 8 style guide
- Use type hints (PEP 484)
- Write docstrings (PEP 257)
- Maintain test coverage above 80%

## Pull Request Process

1. Fork the repository
2. Create a feature branch
3. Write tests for new features
4. Ensure all tests pass
5. Update documentation
6. Submit pull request

[More details...]
```

#### C. CODE_OF_CONDUCT.md

```markdown
# Contributor Code of Conduct

[Standard code of conduct]
```

#### D. CHANGELOG.md

```markdown
# Changelog

All notable changes to Smart Hive AI will be documented here.

## [1.0.0] - 2025-10-16

### Added
- Professional project structure
- Comprehensive documentation
- Test infrastructure
- Code quality tooling

### Changed
- Refactored codebase to follow PEP standards
- Removed informal language and emojis
- Improved error handling and logging

[More entries...]
```

### Step 7: Consolidate Documentation (1 hour)

Merge redundant docs into organized structure:

**docs/troubleshooting/hardware.md:**
- Merge: BME280_TROUBLESHOOTING.md
- Merge: RASPBERRY_PI_ERROR_FIXES.md
- Merge: DOCKER_FIXES.md
- Remove emojis
- Organize by topic

**docs/deployment/raspberry_pi.md:**
- Merge: DEPLOYMENT_GUIDE.md
- Merge: DEPLOYMENT_ISSUES_AND_TFLITE.md
- Professional formatting
- Clear step-by-step instructions

**docs/troubleshooting/common_issues.md:**
- Merge: TROUBLESHOOTING.md
- QUICK_REFERENCE.md content
- Professional tone

### Step 8: Create API Documentation (2 hours)

**docs/api/sensors.md:**
```markdown
# Sensor API Documentation

## BME280 Temperature/Humidity Sensor

### Class: RealBME280

Temperature and humidity sensor interface.

#### Methods

##### get_temp_humidity() -> Tuple[float, float]

Returns current temperature and humidity readings.

**Returns:**
- `temperature` (float): Temperature in Celsius
- `humidity` (float): Relative humidity percentage (0-100)

**Example:**
```python
sensor = RealBME280()
temp, humidity = sensor.get_temp_humidity()
```

[Continue for all sensors...]
```

**docs/api/aws_integration.md:**
[AWS IoT Core, DynamoDB, S3 documentation]

**docs/api/vision.md:**
[Computer vision API documentation]

### Step 9: Test Everything (1 hour)

```bash
# Run code quality checks
pylint src/ --rcfile=.pylintrc
flake8 src/
black --check src/

# Run tests
pytest tests/ -v --cov=src --cov-report=html

# Test on laptop (mock environment)
IS_MOCK_ENVIRONMENT=true python -m src.main

# Build Docker containers
docker compose build

# Test containers
docker compose up -d
docker logs smart-hive-edge
docker logs smart-hive-dashboard
```

### Step 10: Deploy to Raspberry Pi (30 minutes)

```bash
# On laptop: Push changes
git add .
git commit -m "Complete professional refactoring"
git push origin main

# On Raspberry Pi: Pull and rebuild
cd ~/smart-hive-ai
git pull origin main
docker compose down
docker compose build --no-cache
docker compose up -d

# Verify operation
docker logs -f smart-hive-edge
```

### Step 11: Clean Up Old Files (15 minutes)

After verifying everything works:

```bash
# Remove old files (AFTER VERIFICATION!)
rm app.py
rm mock_components.py
rm real_components.py
rm timezone_utils.py
rm check_dynamodb_timestamps.py
rm update_dynamodb_timestamps.py
rm diagnose_dynamodb.py

# Remove redundant docs
rm BME280_TROUBLESHOOTING.md
rm RASPBERRY_PI_ERROR_FIXES.md
rm DOCKER_FIXES.md
rm DEPLOYMENT_ISSUES_AND_TFLITE.md
rm DOC_OVERVIEW.md
rm QUICK_REFERENCE.md
rm TROUBLESHOOTING.md
rm TIMEZONE_CONFIGURATION.md
rm SOUND_AI_INTEGRATION.md

# Keep these (consolidated)
# - README.md (updated)
# - DEPLOYMENT_GUIDE.md (if updated)
# - docs/ folder
```

---

## Time Estimate

| Task | Estimated Time |
|------|----------------|
| Review foundation | 15 min |
| Run migration script | 15 min |
| Refactor Python files | 2 hours |
| Update imports | 30 min |
| Create documentation | 2 hours |
| Consolidate docs | 1 hour |
| API documentation | 2 hours |
| Testing | 1 hour |
| Deploy to Pi | 30 min |
| Cleanup | 15 min |
| **Total** | **9.75 hours** |

Can be done over 2-3 days.

---

## Checklist

### Phase 1: Foundation (DONE)
- [x] Create directory structure
- [x] Create professional src/main.py
- [x] Create test infrastructure
- [x] Create code quality configs
- [x] Create migration script
- [x] Create documentation
- [x] Commit to GitHub

### Phase 2: Migration (TODO)
- [ ] Review foundation documents
- [ ] Run migration script (dry-run)
- [ ] Execute migration
- [ ] Verify directory structure

### Phase 3: Refactoring (TODO)
- [ ] Refactor mock_components.py
- [ ] Refactor real_components.py
- [ ] Refactor timezone_utils.py
- [ ] Refactor config.py
- [ ] Refactor dashboard_app.py
- [ ] Refactor utility scripts

### Phase 4: Documentation (TODO)
- [ ] Rewrite README.md
- [ ] Create CONTRIBUTING.md
- [ ] Create CODE_OF_CONDUCT.md
- [ ] Create CHANGELOG.md
- [ ] Consolidate troubleshooting docs
- [ ] Consolidate deployment docs
- [ ] Create API documentation

### Phase 5: Testing (TODO)
- [ ] Run pylint
- [ ] Run flake8
- [ ] Run black
- [ ] Run pytest
- [ ] Test on laptop
- [ ] Build containers
- [ ] Test containers

### Phase 6: Deployment (TODO)
- [ ] Deploy to Raspberry Pi
- [ ] Verify sensors
- [ ] Verify AWS integration
- [ ] Verify dashboard
- [ ] Monitor for 24 hours

### Phase 7: Cleanup (TODO)
- [ ] Remove old files
- [ ] Remove redundant docs
- [ ] Final commit
- [ ] Update project board

---

## Questions or Issues?

Refer to:
- **PROFESSIONAL_REFACTORING_SUMMARY.md** - Overview
- **REFACTORING_PLAN.md** - Detailed plan
- **src/main.py** - Code example
- **migrate_to_professional_structure.py** - Migration tool

---

## Current Status

**Foundation Complete**: Infrastructure, examples, and tools created.

**Next Action**: Review documents and run migration script.

**Files Ready**: All committed to GitHub and ready for Raspberry Pi deployment.

Good luck with your professional refactoring!
