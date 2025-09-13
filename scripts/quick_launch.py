#!/usr/bin/env python3
"""
Quick launcher scripts for different scanning modes.
"""

import os
import sys
import subprocess
from pathlib import Path


def run_scanner(mode: str, extra_args: list = None):
    """Run the scanner with specified mode."""
    if extra_args is None:
        extra_args = []
    
    # Get project root
    project_root = Path(__file__).parent.parent
    
    # Build command
    cmd = [
        sys.executable, "-m", "src.main",
        "--mode", mode
    ] + extra_args
    
    print(f"🚀 Starting APIKEY-king in {mode} mode...")
    print(f"💻 Command: {' '.join(cmd)}")
    print(f"📁 Working directory: {project_root}")
    print("=" * 50)
    
    # Change to project directory
    os.chdir(project_root)
    
    # Run the scanner
    try:
        subprocess.run(cmd, check=True)
    except KeyboardInterrupt:
        print("\n⛔ Scanning interrupted by user")
    except subprocess.CalledProcessError as e:
        print(f"\n❌ Scanner failed with exit code: {e.returncode}")
        sys.exit(e.returncode)


def main():
    """Main entry point for quick launcher."""
    if len(sys.argv) < 2:
        print("Usage: python scripts/quick_launch.py <mode> [additional_args...]")
        print("Available modes:")
        print("  openrouter    - Scan for OpenRouter API keys only")  
        print("  modelscope    - Scan for ModelScope API keys only")
        print("  gemini        - Scan for Gemini API keys only (with validation)")
        print("  all           - Scan for all types (compatible mode)")
        sys.exit(1)
    
    mode_arg = sys.argv[1].lower()
    extra_args = sys.argv[2:]
    
    # Map friendly names to actual modes
    mode_mapping = {
        "openrouter": "openrouter-only",
        "modelscope": "modelscope-only", 
        "gemini": "gemini-only",
        "all": "compatible"
    }
    
    if mode_arg not in mode_mapping:
        print(f"❌ Unknown mode: {mode_arg}")
        print(f"Available modes: {', '.join(mode_mapping.keys())}")
        sys.exit(1)
    
    actual_mode = mode_mapping[mode_arg]
    run_scanner(actual_mode, extra_args)


if __name__ == "__main__":
    main()