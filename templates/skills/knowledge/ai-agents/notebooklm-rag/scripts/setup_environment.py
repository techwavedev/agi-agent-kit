#!/usr/bin/env python3
"""
Environment Setup for NotebookLM RAG Skill
Creates virtual environment and installs dependencies
"""

import os
import sys
import subprocess
from pathlib import Path


def main():
    skill_dir = Path(__file__).parent.parent
    venv_dir = skill_dir / ".venv"
    requirements_file = skill_dir / "requirements.txt"

    print("🔧 Setting up NotebookLM RAG environment...")

    # Create venv
    print("  📦 Creating virtual environment...")
    subprocess.run([sys.executable, "-m", "venv", str(venv_dir)], check=True)

    # Get venv python
    if os.name == 'nt':
        venv_python = venv_dir / "Scripts" / "python.exe"
        venv_pip = venv_dir / "Scripts" / "pip.exe"
    else:
        venv_python = venv_dir / "bin" / "python"
        venv_pip = venv_dir / "bin" / "pip"

    # Upgrade pip
    print("  📦 Upgrading pip...")
    subprocess.run([str(venv_python), "-m", "pip", "install", "--upgrade", "pip"],
                    capture_output=True)

    # Install requirements
    if requirements_file.exists():
        print("  📦 Installing dependencies...")
        result = subprocess.run(
            [str(venv_pip), "install", "-r", str(requirements_file)],
            capture_output=True, text=True
        )
        if result.returncode != 0:
            print(f"  ❌ Failed to install dependencies: {result.stderr}")
            sys.exit(1)
    else:
        print("  📦 Installing patchright and python-dotenv...")
        subprocess.run(
            [str(venv_pip), "install", "patchright==1.55.2", "python-dotenv==1.0.0"],
            capture_output=True
        )

    # Install Chrome for Patchright
    print("  🌐 Installing Chrome browser...")
    result = subprocess.run(
        [str(venv_python), "-m", "patchright", "install", "chrome"],
        capture_output=True, text=True
    )
    if result.returncode != 0:
        print(f"  ⚠️ Chrome install issue (may already be available): {result.stderr[:200]}")

    print("  ✅ Environment setup complete!")
    return 0


if __name__ == "__main__":
    sys.exit(main())
