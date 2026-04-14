#!/usr/bin/env python3
"""
Cross Tattoos Standalone - One-Time Setup

Ejecutar UNA SOLA VEZ para copiar todos los archivos necesarios:
- CSVs desde el proyecto original
- db_credentials.json
- .env con DEEPSEEK_API_KEY

Uso:
    python setup_data.py
"""

import shutil
from pathlib import Path
import json
import sys

# Add parent directory to path
sys.path.insert(0, str(Path(__file__).parent))


def get_paths():
    """Define all paths."""
    BASE_DIR = Path(__file__).parent
    CONFIG_DIR = BASE_DIR / "config"
    DATA_DIR = BASE_DIR / "data"
    RAW_DIR = DATA_DIR / "raw"
    
    # Original project paths
    ORIGINAL_PROJECT = Path.home() / "PycharmProjects" / "HopeisHope"
    ORIGINAL_CSV_DIR = ORIGINAL_PROJECT / "csv" / "equi"
    
    return {
        'BASE_DIR': BASE_DIR,
        'CONFIG_DIR': CONFIG_DIR,
        'RAW_DIR': RAW_DIR,
        'ORIGINAL_PROJECT': ORIGINAL_PROJECT,
        'ORIGINAL_CSV_DIR': ORIGINAL_CSV_DIR,
    }


def setup_directories(paths):
    """Create all required directories."""
    print("\n📁 Creating directories...")
    
    dirs = [
        paths['RAW_DIR'],
        paths['BASE_DIR'] / "data" / "processed",
        paths['BASE_DIR'] / "data" / "output",
        paths['BASE_DIR'] / "data" / "cross_examples",
    ]
    
    for d in dirs:
        d.mkdir(parents=True, exist_ok=True)
        print(f"  ✓ {d}")


def copy_db_credentials(paths):
    """Copy db_credentials.json from original project."""
    print("\n🔐 Setting up database credentials...")
    
    source = paths['ORIGINAL_PROJECT'] / "db_credentials.json"
    dest = paths['CONFIG_DIR'] / "db_credentials.json"
    
    if dest.exists():
        print(f"  ⚠️  Already exists: {dest}")
        return True
    
    if source.exists():
        shutil.copy2(source, dest)
        print(f"  ✓ Copied from: {source}")
        return True
    else:
        print(f"  ✗ Not found: {source}")
        print(f"    Please create manually: {dest}")
        return False


def setup_env_file(paths):
    """Create .env file with DEEPSEEK_API_KEY placeholder."""
    print("\n🔑 Setting up .env file...")
    
    env_file = paths['CONFIG_DIR'] / ".env"
    
    if env_file.exists():
        print(f"  ⚠️  Already exists: {env_file}")
        return True
    
    # Check if there's an existing .env in original project
    original_env = paths['ORIGINAL_PROJECT'] / ".env"
    
    if original_env.exists():
        shutil.copy2(original_env, env_file)
        print(f"  ✓ Copied from: {original_env}")
        return True
    
    # Create new .env with placeholder
    content = """# Cross Tattoos Standalone - Environment Variables
# Edit this file with your API keys

DEEPSEEK_API_KEY=your_deepseek_api_key_here
GOOGLE_API_KEY=your_google_api_key_here
"""
    env_file.write_text(content)
    print(f"  ✓ Created: {env_file}")
    print(f"    ⚠️  Edit this file to add your API keys")
    return True


def copy_csvs(paths):
    """Copy CSV files from original project."""
    print("\n📊 Copying CSV files...")
    
    csv_files = [
        "pfsi_v2_principal.csv",
        "repd_vp_cedulas_principal.csv",
        "repd_vp_cedulas_senas.csv",
        "repd_vp_cedulas_vestimenta.csv",
    ]
    
    copied = 0
    
    for filename in csv_files:
        source = paths['ORIGINAL_CSV_DIR'] / filename
        dest = paths['RAW_DIR'] / filename
        
        if dest.exists():
            print(f"  ⚠️  Already exists: {filename}")
            copied += 1
            continue
        
        if source.exists():
            shutil.copy2(source, dest)
            size_mb = source.stat().st_size / (1024 * 1024)
            print(f"  ✓ {filename} ({size_mb:.1f} MB)")
            copied += 1
        else:
            print(f"  ✗ Not found: {source}")
    
    return copied == len(csv_files)


def main():
    """Run complete one-time setup."""
    print("=" * 60)
    print("CROSS TATTOOS STANDALONE - ONE-TIME SETUP")
    print("=" * 60)
    
    paths = get_paths()
    
    # Show detected paths
    print("\n🔍 Detected paths:")
    print(f"  - Original project: {paths['ORIGINAL_PROJECT']}")
    print(f"  - Original CSVs:    {paths['ORIGINAL_CSV_DIR']}")
    print(f"  - Target data:      {paths['RAW_DIR']}")
    
    # Check if original project exists
    if not paths['ORIGINAL_PROJECT'].exists():
        print(f"\n⚠️  Original project not found at: {paths['ORIGINAL_PROJECT']}")
        print("   You may need to adjust the paths in this script.")
        return
    
    # Run setup steps
    setup_directories(paths)
    db_ok = copy_db_credentials(paths)
    env_ok = setup_env_file(paths)
    csv_ok = copy_csvs(paths)
    
    # Summary
    print("\n" + "=" * 60)
    print("SETUP COMPLETE")
    print("=" * 60)
    
    if db_ok and env_ok and csv_ok:
        print("✓ All files copied successfully!")
        print("\nNext steps:")
        print("  1. Edit config/.env with your DEEPSEEK_API_KEY")
        print("  2. Run: python cli.py setup")
        print("  3. Run: python cli.py run-all --skip-mine --skip-export")
    else:
        print("⚠️  Some files were not found. Check the paths above.")
        print("\nMissing files can be copied manually to:")
        print(f"  - CSVs:        {paths['RAW_DIR']}")
        print(f"  - Credentials: {paths['CONFIG_DIR']}")


if __name__ == "__main__":
    main()
