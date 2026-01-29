#!/usr/bin/env python3
"""
LANrage setup script
Handles initial setup and dependency installation
"""

import subprocess
import sys
from pathlib import Path


def run_command(cmd: list[str], check: bool = True) -> bool:
    """Run a command and return success status"""
    try:
        result = subprocess.run(cmd, check=check, capture_output=True, text=True)
        return result.returncode == 0
    except subprocess.CalledProcessError as e:
        print(f"❌ Command failed: {' '.join(cmd)}")
        print(f"   Error: {e.stderr}")
        return False


def main():
    print("🔥 LANrage Setup")
    print("=" * 60)
    
    # Check Python version
    if sys.version_info < (3, 12):
        print("❌ Python 3.12 or higher required")
        print(f"   Current version: {sys.version}")
        sys.exit(1)
    print("✓ Python version OK")
    
    # Check if uv is installed
    if not run_command(["uv", "--version"], check=False):
        print("❌ uv not found")
        print("   Install from: https://docs.astral.sh/uv/")
        sys.exit(1)
    print("✓ uv found")
    
    # Create virtual environment
    venv_path = Path(".venv")
    if not venv_path.exists():
        print("Creating virtual environment...")
        if not run_command(["uv", "venv", "--python", "3.12"]):
            sys.exit(1)
        print("✓ Virtual environment created")
    else:
        print("✓ Virtual environment exists")
    
    # Install dependencies
    print("Installing dependencies...")
    if not run_command(["uv", "pip", "install", "-r", "requirements.txt"]):
        sys.exit(1)
    print("✓ Dependencies installed")
    
    # Create .env if it doesn't exist
    env_path = Path(".env")
    if not env_path.exists():
        print("Creating .env file...")
        env_path.write_text(Path(".env.example").read_text())
        print("✓ .env created")
    
    print("\n" + "=" * 60)
    print("✅ Setup complete!")
    print("\nNext steps:")
    print("  1. Activate virtual environment:")
    print("     Windows: .venv\\Scripts\\activate.bat")
    print("     Linux/Mac: source .venv/bin/activate")
    print("  2. Run LANrage:")
    print("     python lanrage.py")
    print("  3. Open browser:")
    print("     http://localhost:8666")


if __name__ == "__main__":
    main()
