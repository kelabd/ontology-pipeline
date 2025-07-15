# test_setup.py - Simple setup test without API calls
import os
from pathlib import Path
import json
import sys

# Set up path for imports
project_root = Path(__file__).parent
sys.path.append(str(project_root))

def test_basic_setup():
    print("🧪 Testing Basic Setup")
    print("=" * 30)
    
    # Check project structure
    required_folders = ['src', 'config', 'data']
    for folder in required_folders:
        if Path(folder).exists():
            print(f"✅ {folder}/ folder exists")
        else:
            print(f"❌ {folder}/ folder missing")
            Path(folder).mkdir(exist_ok=True)
            print(f"  Created {folder}/ folder")
    
    # Check for .env file
    env_file = Path('.env')
    if env_file.exists():
        print("✅ .env file exists")
        # Try to read API key
        with open(env_file, 'r') as f:
            content = f.read()
            if 'ANTHROPIC_API_KEY' in content:
                print("✅ API key found in .env")
            else:
                print("❌ API key not found in .env")
    else:
        print("❌ .env file missing")
    
    # Check if we can import our modules (without anthropic)
    try:
        from config.ontology_schema import ONTOLOGY_SCHEMA
        print("✅ ontology_schema.py imports successfully")
        print(f"  Found {len(ONTOLOGY_SCHEMA['domains'])} domains")
    except ImportError as e:
        print(f"❌ ontology_schema.py import failed: {e}")
    
    print("\n🎯 Basic setup test complete!")
    print("Once you fix the anthropic package, run test_simple.py")

if __name__ == "__main__":
    test_basic_setup()