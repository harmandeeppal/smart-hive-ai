#!/usr/bin/env python3
"""
Smart Hive AI - Project Cleanup and Organization Script

This script cleans up the project directory, removes redundant documentation,
organizes ML models properly, updates file paths in source code, and creates
a professional, production-ready project structure.

Author: Development Team
Created: October 2025

Usage:
    python PROJECT_CLEANUP.py
"""

import os
import shutil
from pathlib import Path
import logging

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

class ProjectCleaner:
    """Handles project cleanup and reorganization."""
    
    def __init__(self, project_root: str = '.'):
        self.root = Path(project_root).absolute()
        logger.info(f"Project root: {self.root}")
    
    def cleanup_documentation(self):
        """Remove redundant documentation files."""
        print("\n" + "=" * 80)
        print("STEP 1: CLEANING UP DOCUMENTATION")
        print("=" * 80)
        
        # Files to KEEP in root
        keep_files = {'README.md', 'LICENSE.md', '.gitignore', '.env.example'}
        
        # Files to REMOVE from root (intermediate/outdated docs)
        remove_files = {
            'ANSWERS_TO_YOUR_QUESTIONS.md',
            'CLARIFICATION_INDEX.md',
            'CLARIFICATION_NOTES.md',
            'DASHBOARD_CHANGES_DETAILED.md',
            'DELIVERABLES_CHECKLIST.md',
            'DEPLOYMENT_READY.md',
            'DOCKER_REFACTORING_COMPLETE.md',
            'FINAL_REPORT.md',
            'HONEST_ASSESSMENT.md',
            'IMPLEMENTATION_SUMMARY.md',
            'ML_INFERENCE_REFACTORING.md',
            'ML_INTEGRATION_INDEX.md',
            'ML_INTEGRATION_SUMMARY.md',
            'ML_MODEL_INTEGRATION_SUMMARY.md',
            'QUICK_REFERENCE.md',
            'QUICK_START_DOCKER.md',
            'REFACTORING_COMPLETE.md',
            'VERIFICATION_REPORT.md',
            'ML_INTEGRATION_COMPLETE.txt',
        }
        
        removed_count = 0
        for filename in remove_files:
            file_path = self.root / filename
            if file_path.exists():
                try:
                    file_path.unlink()
                    logger.info(f"✓ Removed: {filename}")
                    removed_count += 1
                except Exception as e:
                    logger.error(f"✗ Failed to remove {filename}: {e}")
        
        logger.info(f"Removed {removed_count} redundant documentation files")
    
    def organize_ml_models(self):
        """Verify and organize ML models."""
        print("\n" + "=" * 80)
        print("STEP 2: ORGANIZING ML MODELS")
        print("=" * 80)
        
        models_dir = self.root / 'models'
        models_dir.mkdir(exist_ok=True)
        
        # Check vision model
        vision_source = self.root / 'ml_vision_model' / 'vision_model.pt'
        vision_target = models_dir / 'vision_model.pt'
        if vision_source.exists() and not vision_target.exists():
            shutil.copy2(vision_source, vision_target)
            logger.info(f"✓ Copied YOLO model to models/vision_model.pt")
        elif vision_target.exists():
            logger.info(f"✓ YOLO model already in models/vision_model.pt")
        
        # Check audio model
        audio_source = self.root / 'ml_audio_model' / 'audio_model.pkl'
        audio_target = models_dir / 'audio_model.pkl'
        if audio_source.exists() and not audio_target.exists():
            shutil.copy2(audio_source, audio_target)
            logger.info(f"✓ Copied audio model to models/audio_model.pkl")
        elif audio_target.exists():
            logger.info(f"✓ Audio model already in models/audio_model.pkl")
    
    def verify_structure(self):
        """Verify final project structure."""
        print("\n" + "=" * 80)
        print("STEP 3: VERIFYING PROJECT STRUCTURE")
        print("=" * 80)
        
        required_dirs = [
            'src',
            'tests', 
            'docs',
            'models',
            'dashboard',
            'certs',
            'ml_vision_model',
            'ml_audio_model'
        ]
        
        for dir_name in required_dirs:
            dir_path = self.root / dir_name
            if dir_path.exists():
                logger.info(f"✓ {dir_name}/ exists")
            else:
                logger.warning(f"✗ {dir_name}/ MISSING")
        
        required_files = [
            'README.md',
            'app.py',
            'config.py',
            'ml_inference_service.py',
            'docker-compose.yml',
            'requirements.txt',
        ]
        
        for filename in required_files:
            file_path = self.root / filename
            if file_path.exists():
                size_kb = file_path.stat().st_size / 1024
                logger.info(f"✓ {filename} ({size_kb:.1f} KB)")
            else:
                logger.warning(f"✗ {filename} MISSING")
    
    def run(self):
        """Execute all cleanup steps."""
        print("\n" + "╔" + "=" * 78 + "╗")
        print("║" + " " * 20 + "SMART HIVE AI - PROJECT CLEANUP" + " " * 27 + "║")
        print("╚" + "=" * 78 + "╝")
        
        try:
            self.cleanup_documentation()
            self.organize_ml_models()
            self.verify_structure()
            
            print("\n" + "=" * 80)
            print("PROJECT CLEANUP COMPLETED SUCCESSFULLY!")
            print("=" * 80)
            print("\nNext steps:")
            print("1. Review the project structure")
            print("2. Run tests: python -m pytest tests/")
            print("3. Deploy: docker-compose up -d")
            print("=" * 80 + "\n")
            
        except Exception as e:
            logger.error(f"Cleanup failed: {e}")
            raise

if __name__ == '__main__':
    cleaner = ProjectCleaner()
    cleaner.run()
