#!/usr/bin/env python3
"""
Clear Streamlit Cache
=====================

This script clears the Streamlit cache to force fresh data pulls.
Run this after updating the code to ensure new calculations are used.

Usage:
    python clear_cache.py
"""

import os
import shutil
from pathlib import Path

def clear_streamlit_cache():
    """Clear Streamlit's cache directory."""
    # Streamlit cache locations
    cache_locations = [
        Path.home() / ".streamlit" / "cache",
        Path(".streamlit") / "cache",
        Path(".") / ".streamlit" / "cache",
    ]
    
    cleared = False
    for cache_path in cache_locations:
        if cache_path.exists():
            print(f"📁 Found cache at: {cache_path}")
            try:
                shutil.rmtree(cache_path)
                print(f"✅ Cleared cache: {cache_path}")
                cleared = True
            except Exception as e:
                print(f"⚠️  Could not clear {cache_path}: {e}")
    
    if not cleared:
        print("ℹ️  No cache directories found (cache may already be clear)")
    
    return cleared


def clear_csv_cache():
    """Clear CSV data cache."""
    data_dir = Path("data")
    if data_dir.exists():
        csv_files = list(data_dir.glob("*_cached.csv"))
        if csv_files:
            print(f"\n📊 Found {len(csv_files)} cached CSV files")
            response = input("Clear CSV cache too? (y/N): ")
            if response.lower() == 'y':
                for csv_file in csv_files:
                    try:
                        csv_file.unlink()
                        print(f"✅ Deleted: {csv_file.name}")
                    except Exception as e:
                        print(f"⚠️  Could not delete {csv_file.name}: {e}")
                print(f"✅ Cleared {len(csv_files)} CSV files")
            else:
                print("ℹ️  Kept CSV cache (will use existing data)")
        else:
            print("\nℹ️  No CSV cache files found")
    else:
        print("\nℹ️  No data directory found")


def main():
    """Main entry point."""
    print("\n" + "="*60)
    print("TECTONIQ - Cache Cleaner")
    print("="*60 + "\n")
    
    print("This will clear cached data to force fresh calculations.")
    print("Run this after updating the code to see changes immediately.\n")
    
    # Clear Streamlit cache
    print("🧹 Clearing Streamlit cache...")
    cleared_st = clear_streamlit_cache()
    
    # Clear CSV cache (optional)
    clear_csv_cache()
    
    # Summary
    print("\n" + "="*60)
    print("✅ Cache clearing complete!")
    print("="*60)
    print("\nNext steps:")
    print("1. Restart the Streamlit app: streamlit run app.py")
    print("2. Search for any ticker (e.g., AAPL)")
    print("3. Check if 24h change now shows correctly")
    print("\n" + "="*60 + "\n")


if __name__ == "__main__":
    main()

