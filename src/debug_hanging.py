#!/usr/bin/env python3
"""
Debug script for hanging automation issue.

This script runs a single prompt automation with enhanced logging
to help identify where the hanging occurs.
"""

import sys
import os
from pathlib import Path

# Add src to path
sys.path.insert(0, str(Path(__file__).parent / "src"))

from automator import run_single_prompt_automation
from ui.session_app import RefactoredSessionUI
import logging

# Set up enhanced logging
logging.basicConfig(
    level=logging.DEBUG,
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
    handlers=[
        logging.FileHandler("debug_hanging.log"),
        logging.StreamHandler(),
    ],
)

def main():
    """Run single prompt automation with debugging."""
    print("🔍 Starting hanging debug test...")
    
    # Create UI with test settings
    ui = RefactoredSessionUI(
        start_delay=2,
        main_wait=5,
        cooldown=3,
        get_ready_delay=2
    )
    
    # Set test prompts
    ui.prompts = [
        "This is a test prompt for debugging the hanging issue.",
        "Second test prompt to verify the issue.",
        "Third test prompt to continue testing."
    ]
    
    # Set test coordinates (you'll need to update these)
    ui.coords = {
        "input": (100, 200),
        "submit": (300, 200),
        "accept": (500, 200)
    }
    
    print(f"📋 Test setup:")
    print(f"   Prompts: {len(ui.prompts)}")
    print(f"   Coordinates: {ui.coords}")
    print(f"   Timers: {ui.get_timers()}")
    
    # Run single prompt automation
    print("\n🚀 Starting single prompt automation...")
    success = run_single_prompt_automation(ui, 0)
    
    print(f"\n✅ Automation result: {'SUCCESS' if success else 'FAILED'}")
    
    if not success:
        print("❌ Automation failed - check debug_hanging.log for details")
    else:
        print("✅ Automation completed successfully")
    
    ui.close()

if __name__ == "__main__":
    main()
