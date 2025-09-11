#!/usr/bin/env python3
"""
Version synchronization script for pyzxing.

This script updates version numbers across all configuration files
to maintain consistency.
"""

import re
import sys
from pathlib import Path

def update_version(new_version):
    """Update version in all relevant files."""
    
    # Update __version__.py
    version_file = Path("pyzxing/__version__.py")
    version_file.write_text(f'"""Version information for pyzxing package."""\n\n__version__ = "{new_version}"\n\n# For backward compatibility\nVERSION = __version__\n')
    
    # Update conda-recipe/meta.yaml
    conda_file = Path("conda-recipe/meta.yaml")
    if conda_file.exists():
        content = conda_file.read_text()
        replacement = f'{{% set version = "{new_version}" %}} {{# Sync with pyzxing/__version__.py #}}'
        content = re.sub(r'{% set version = ".*?" %}', replacement, content)
        conda_file.write_text(content)
    
    print(f"✅ Updated version to {new_version}")

def check_version_consistency():
    """Check if versions are consistent across files."""
    try:
        # Get version from __version__.py
        version_file = Path("pyzxing/__version__.py")
        version_content = version_file.read_text()
        version_match = re.search(r'__version__ = ["\']([^"\']+)["\']', version_content)
        if not version_match:
            print("❌ Could not find version in __version__.py")
            return False
        
        main_version = version_match.group(1)
        print(f"📋 Main version: {main_version}")
        
        # Check conda-recipe/meta.yaml
        conda_file = Path("conda-recipe/meta.yaml")
        if conda_file.exists():
            conda_content = conda_file.read_text()
            conda_match = re.search(r'{% set version = ["\']([^"\']+)["\']', conda_content)
            if conda_match:
                conda_version = conda_match.group(1)
                if conda_version != main_version:
                    print(f"❌ Version mismatch in conda-recipe/meta.yaml: {conda_version}")
                    return False
                else:
                    print(f"✅ conda-recipe/meta.yaml: {conda_version}")
        
        print("✅ All versions are consistent!")
        return True
        
    except Exception as e:
        print(f"❌ Error checking versions: {e}")
        return False

if __name__ == "__main__":
    if len(sys.argv) == 2:
        # Update version
        new_version = sys.argv[1]
        update_version(new_version)
    elif len(sys.argv) == 1:
        # Check consistency
        check_version_consistency()
    else:
        print("Usage:")
        print("  python scripts/version_sync.py                    # Check version consistency")
        print("  python scripts/version_sync.py <new_version>   # Update all versions")
        sys.exit(1)