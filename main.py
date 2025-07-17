#!/usr/bin/env python3
"""
Bash Script CLI Tool - Main Entry Point
Interactive CLI tool for writing, managing, and executing bash scripts.
"""

import sys
import os
from pathlib import Path
import argparse
from cli import BashScriptCLI

def main():
    """Main entry point for the bash script CLI tool."""
    parser = argparse.ArgumentParser(
        description="Interactive CLI tool for writing, managing, and executing bash scripts"
    )
    parser.add_argument(
        "--script-dir",
        default="./scripts",
        help="Directory to store saved scripts (default: ./scripts)"
    )
    parser.add_argument(
        "--version",
        action="version",
        version="Bash Script CLI Tool v1.0.0"
    )
    
    args = parser.parse_args()
    
    # Ensure script directory exists
    script_dir = Path(args.script_dir)
    script_dir.mkdir(exist_ok=True)
    
    # Initialize and start the CLI
    try:
        cli = BashScriptCLI(script_dir)
        cli.run()
    except KeyboardInterrupt:
        print("\n\nGoodbye!")
        sys.exit(0)
    except Exception as e:
        print(f"Error: {e}")
        sys.exit(1)

if __name__ == "__main__":
    main()
