#!/usr/bin/env python3
"""
Smart Hive AI - Directory Analysis & Cleanup Recommendations

This script analyzes the project structure and recommends what to keep/remove.
"""

import os
from pathlib import Path
from datetime import datetime

print("\n" + "=" * 80)
print("SMART HIVE AI - DIRECTORY & FILE ANALYSIS")
print("=" * 80)

# ============================================================================
# SECTION 1: ML_VISION_MODEL ANALYSIS
# ============================================================================
print("\n" + "╔" + "=" * 78 + "╗")
print("║ 1. ML_VISION_MODEL DIRECTORY                                              ║")
print("╚" + "=" * 78 + "╝")

print("""
CONTENTS:
  ✓ best.pt (6.23 MB) - YOLO v8 Model
    └─ ESSENTIAL: Pre-trained vision detection model (queen bee detector)
    
  ✓ vision_processor.py (8.2 KB)
    └─ ESSENTIAL: Core ML processor that loads & uses best.pt
    └─ Contains: VisionProcessor class with process_frame() method
    
  ✓ camera_yolo_noir.py
    └─ REFERENCE: Example Raspberry Pi camera implementation
    └─ Can be archived if not needed
    
  ✓ libcamera/ (build system files)
    └─ NOT NEEDED: libcamera build system for Raspberry Pi camera
    └─ This is development cruft - can be safely deleted
    
  ✓ inputs/ & outputs/
    └─ TEMPORARY: Folder for image processing samples
    └─ Safe to delete after development

RECOMMENDATION:
  KEEP:
    • best.pt
    • vision_processor.py
  
  CAN DELETE:
    • libcamera/ (not needed in production)
    • camera_yolo_noir.py (just reference code)
    • inputs/ & outputs/ (temporary working dirs)
""")

# ============================================================================
# SECTION 2: ML_AUDIO_MODEL ANALYSIS
# ============================================================================
print("\n" + "╔" + "=" * 78 + "╗")
print("║ 2. ML_AUDIO_MODEL DIRECTORY                                               ║")
print("╚" + "=" * 78 + "╝")

print("""
CONTENTS:
  ✓ queen_bee_model.pkl (15.8 MB) - Audio Classification Model
    └─ ESSENTIAL: Scikit-learn model for queen bee sound detection
    
  ✓ audio_processor.py (11.6 KB)
    └─ ESSENTIAL: Core ML processor that loads & uses queen_bee_model.pkl
    └─ Contains: AudioProcessor class with record_and_classify() method
    
  ✓ enhanced_queen_bee_detection.py
    └─ REFERENCE: Training script that created the .pkl model
    └─ Used during development, not needed in production
    
  ✓ Figure_1.png & Figure_2.png
    └─ REFERENCE: Training charts/graphs
    └─ Documentation only, can be archived
    
  ✓ How to Run On Pi.docx
    └─ OUTDATED: Old setup documentation
    └─ Superseded by docs/SETUP_AND_DEPLOYMENT.md
    
  ✓ Other Files/
    └─ UNKNOWN: Empty or leftover directory
    └─ Safe to delete

RECOMMENDATION:
  KEEP:
    • queen_bee_model.pkl
    • audio_processor.py
  
  CAN DELETE:
    • enhanced_queen_bee_detection.py (training script, not needed)
    • Figure_1.png & Figure_2.png (just charts)
    • How to Run On Pi.docx (outdated)
    • Other Files/ (cleanup)
""")

# ============================================================================
# SECTION 3: DOCS FOLDER ANALYSIS
# ============================================================================
print("\n" + "╔" + "=" * 78 + "╗")
print("║ 3. DOCS FOLDER ANALYSIS                                                   ║")
print("╚" + "=" * 78 + "╝")

docs_analysis = {
    "ESSENTIAL (Keep)": {
        "DEPLOYMENT.md": "Production deployment procedures & Docker setup",
        "SETUP_AND_DEPLOYMENT.md": "Complete setup guide from scratch",
        "TROUBLESHOOTING.md": "Common issues & solutions",
        "CONFIGURATION_GUIDE.md": "Environment variables & config options",
    },
    "GOOD REFERENCE (Keep)": {
        "ML_IMPLEMENTATION_CHECKLIST.md": "Verification that ML is working",
        "ML_MODELS_IMPLEMENTATION_GUIDE.md": "How ML models are integrated",
    },
    "OPTIONAL/OUTDATED (Can Delete)": {
        "CONTINUOUS_AI_VISION.md": "Development notes (outdated)",
        "DOCKER_ARCHITECTURE.md": "Architecture diagram (superseded)",
        "IMPLEMENTATION_SUMMARY.md": "Old summary (not up to date)",
        "ML_ARCHITECTURE_DIAGRAMS.md": "Diagram references (outdated)",
        "ML_INTEGRATION_PLAN.md": "Planning document (completed)",
        "ML_QUICK_START.md": "Quick start (integrated in SETUP)",
        "ML_VISUAL_SUMMARY.md": "Visual summary (reference only)",
        "PROJECT_PLAN.md": "Project planning (archived)",
        "VIDEO_STREAM_CONFIGURATION.md": "Specific to video setup",
    },
    "SUBDIRECTORIES": {
        "api/": "API documentation subdirectory (can be kept or removed)",
        "deployment/": "Deployment scripts/configs (useful to keep)",
        "troubleshooting/": "Troubleshooting guides (useful to keep)",
    }
}

for category, items in docs_analysis.items():
    print(f"\n{category}:")
    for file_name, description in items.items():
        status = "✓" if "Keep" in category else "○" if "Optional" in category else "→"
        print(f"  {status} {file_name:<35} {description}")

print("""

RECOMMENDATION - KEEP THESE (Minimum):
  • DEPLOYMENT.md (production guide)
  • SETUP_AND_DEPLOYMENT.md (setup from scratch)
  • TROUBLESHOOTING.md (problem solving)
  • CONFIGURATION_GUIDE.md (environment setup)
  • deployment/ (deployment scripts)
  • troubleshooting/ (specific troubleshooting guides)

RECOMMENDATION - CAN DELETE (Clutter):
  • CONTINUOUS_AI_VISION.md (old notes)
  • DOCKER_ARCHITECTURE.md (outdated)
  • IMPLEMENTATION_SUMMARY.md (stale)
  • ML_ARCHITECTURE_DIAGRAMS.md (diagram refs)
  • ML_INTEGRATION_PLAN.md (completed task)
  • ML_QUICK_START.md (merged into SETUP)
  • ML_VISUAL_SUMMARY.md (reference only)
  • PROJECT_PLAN.md (archived)
  • VIDEO_STREAM_CONFIGURATION.md (specific)
""")

# ============================================================================
# SECTION 4: FILE RENAMING ANALYSIS
# ============================================================================
print("\n" + "╔" + "=" * 78 + "╗")
print("║ 4. FILE RENAMING ANALYSIS (Your Question)                                 ║")
print("╚" + "=" * 78 + "╝")

print("""
YOU ASKED: Rename best.pt to vision_model.py?
ANSWER: NO - This would be WRONG! Here's why:

  best.pt IS A MODEL FILE, NOT PYTHON CODE
  ✗ Wrong:  vision_model.py (suggests it's Python code)
  ✓ Right:  best.pt (YOLO model format)
  
  The .pt extension means PyTorch model
  Python would fail to load it if named .py
  
BETTER NAMING (if you want to rename):
  • best.pt         → vision_model.pt (or yolo_model.pt)
  • best.pt         → keep as is (RECOMMENDED)

YOU ASKED: Rename queen_bee_model.pkl to audio_model.pkl?
ANSWER: YES - This makes sense!

  ✓ queen_bee_model.pkl → audio_model.pkl (shorter, clearer)
  
  The .pkl extension stays (Python pickle format)
  Shorter filename is better
  
VERDICT:
  ✗ DO NOT rename:  best.pt → vision_model.py
  ✓ CAN rename:     queen_bee_model.pkl → audio_model.pkl
""")

# ============================================================================
# SECTION 5: SUMMARY & RECOMMENDATIONS
# ============================================================================
print("\n" + "╔" + "=" * 78 + "╗")
print("║ 5. FINAL RECOMMENDATIONS                                                  ║")
print("╚" + "=" * 78 + "╝")

print("""
PROJECT STRUCTURE CLEANUP PLAN:

1. ML_VISION_MODEL:
   ✓ KEEP: best.pt, vision_processor.py
   ✓ DELETE: libcamera/, camera_yolo_noir.py, inputs/, outputs/

2. ML_AUDIO_MODEL:
   ✓ KEEP: queen_bee_model.pkl, audio_processor.py
   ✓ DELETE: enhanced_queen_bee_detection.py, *.png, *.docx, Other Files/
   ✓ RENAME: queen_bee_model.pkl → audio_model.pkl
   ✓ UPDATE CODE: Update imports from "queen_bee_model.pkl" → "audio_model.pkl"

3. DOCS FOLDER:
   ✓ KEEP: DEPLOYMENT.md, SETUP_AND_DEPLOYMENT.md, TROUBLESHOOTING.md,
            CONFIGURATION_GUIDE.md, deployment/, troubleshooting/
   ✓ DELETE: Old planning/architectural docs (see list above)
   ✓ KEEP: ML_IMPLEMENTATION_CHECKLIST.md, ML_MODELS_IMPLEMENTATION_GUIDE.md

4. MODELS DIRECTORY (shared location):
   ✓ KEEP: Copy of best.pt, audio_model.pkl (after renaming)
   ✓ PURPOSE: Single location for all models
""")

print("\n" + "=" * 80)
print("ANALYSIS COMPLETE")
print("=" * 80 + "\n")
