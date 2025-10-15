"""
Smart Hive AI - Project Cleanup Script

Description:
    Removes redundant documentation files that have been consolidated into
    the docs/ directory. This script helps maintain a clean project structure.

Author: Smart Hive AI Team
Created: October 2025

Usage:
    python scripts/cleanup_redundant_files.py
    
    Review the list of files to be removed before confirming deletion.
"""

import os
from pathlib import Path

def main():
    """Remove redundant documentation files after consolidation."""
    
    base_dir = Path(__file__).parent.parent
    
    # List of redundant files to remove
    redundant_files = [
        "ACTION_PLAN.md",
        "BME280_TROUBLESHOOTING.md",
        "DEPLOYMENT_ISSUES_AND_TFLITE.md",
        "DOCKER_FIXES.md",
        "DOC_OVERVIEW.md",
        "QUICK_REFERENCE.md",
        "RASPBERRY_PI_ERROR_FIXES.md",
        "SOUND_AI_INTEGRATION.md",
        "TIMEZONE_CONFIGURATION.md",
        "TROUBLESHOOTING.md",  # Root version, kept in docs/
        "DEPLOYMENT_GUIDE.md",  # Root version, kept in docs/
        "REFACTORING_PLAN.md",
        "REFACTORING_CHECKLIST.md"
    ]
    
    print("=" * 80)
    print("SMART HIVE AI - PROJECT CLEANUP")
    print("=" * 80)
    print()
    print("This script will remove the following redundant files:")
    print("(Content has been consolidated into docs/ directory)")
    print()
    
    existing_files = []
    for file in redundant_files:
        file_path = base_dir / file
        if file_path.exists():
            existing_files.append(file_path)
            size = file_path.stat().st_size / 1024  # Size in KB
            print(f"  - {file} ({size:.1f} KB)")
    
    if not existing_files:
        print("No redundant files found. Project already cleaned up!")
        return
    
    print()
    print(f"Total files to remove: {len(existing_files)}")
    print()
    
    response = input("Do you want to proceed with deletion? (yes/no): ").lower()
    
    if response == 'yes':
        print()
        print("Removing files...")
        for file_path in existing_files:
            try:
                os.remove(file_path)
                print(f"  Removed: {file_path.name}")
            except Exception as e:
                print(f"  Error removing {file_path.name}: {e}")
        
        print()
        print("=" * 80)
        print("Cleanup completed successfully!")
        print("=" * 80)
        print()
        print("Consolidated documentation is available in:")
        print("  - docs/TROUBLESHOOTING.md")
        print("  - docs/DEPLOYMENT.md")
        print("  - docs/CONFIGURATION_GUIDE.md")
        print("  - README_PROFESSIONAL.md")
    else:
        print()
        print("Cleanup cancelled. No files were removed.")

if __name__ == "__main__":
    main()
