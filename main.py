# main.py
"""
Main script to process all transcripts in the data/transcripts folder
Now with extractor selection capability
"""

import os
from pathlib import Path
import json
import sys

# Set up path for imports
project_root = Path(__file__).parent
sys.path.append(str(project_root))

from src.extractor import create_extractor, OntologyExtractor, RobustOntologyExtractor

def main():
    print("🚀 Ontology Extraction Pipeline")
    print("=" * 50)
    
    # Check API key
    api_key = os.getenv('ANTHROPIC_API_KEY')
    if not api_key:
        # Try to load from .env file manually
        env_file = Path('.env')
        if env_file.exists():
            with open(env_file, 'r') as f:
                for line in f:
                    if line.startswith('ANTHROPIC_API_KEY='):
                        api_key = line.split('=', 1)[1].strip()
                        os.environ['ANTHROPIC_API_KEY'] = api_key
                        break
    
    if not api_key:
        print("❌ No API key found!")
        print("Make sure you created the .env file with your API key")
        return
    
    # Extractor selection
    print("\n🔧 EXTRACTOR SELECTION:")
    print("1. Standard (4-pass) - Original extraction method")
    print("2. Robust (7-pass) - Enhanced comprehensive extraction")
    print("3. Auto-select based on file count")
    
    try:
        choice = input("\nChoose extractor (1/2/3) [default: 2]: ").strip()
        if not choice:
            choice = "2"
    except:
        choice = "2"  # Default for non-interactive environments
    
    # Initialize extractor based on choice
    try:
        if choice == "1":
            extractor = OntologyExtractor(api_key=api_key)
        elif choice == "3":
            # Auto-select based on file count
            transcript_folder = "data/transcripts"
            if Path(transcript_folder).exists():
                file_count = len(list(Path(transcript_folder).glob("*.txt")))
                if file_count <= 3:
                    print("📊 Auto-selecting Robust extractor (≤3 files)")
                    extractor = RobustOntologyExtractor(api_key=api_key)
                else:
                    print("📊 Auto-selecting Standard extractor (>3 files)")
                    extractor = OntologyExtractor(api_key=api_key)
            else:
                extractor = RobustOntologyExtractor(api_key=api_key)
        else:  # Default to robust
            extractor = RobustOntologyExtractor(api_key=api_key)
            
    except Exception as e:
        print(f"❌ Failed to initialize extractor: {e}")
        return
    
    # Set transcript folder
    transcript_folder = "data/transcripts"
    
    # Check if folder exists and has files
    if not Path(transcript_folder).exists():
        print(f"❌ Transcript folder not found: {transcript_folder}")
        print("Creating folder... Please add your .txt transcript files there.")
        Path(transcript_folder).mkdir(parents=True, exist_ok=True)
        return
    
    # Process transcripts
    try:
        results = extractor.process_transcript_folder(transcript_folder)
        
        if "error" in results:
            print(f"❌ Processing failed: {results['error']}")
            return
        
        # Save results
        output_path = extractor.save_results(results)
        
        # Save results
        output_path = extractor.save_results(results)
        
        # Print summary
        print("\n" + "=" * 50)
        print("✅ EXTRACTION COMPLETE!")
        print(f"🔧 Extractor used: {results['summary'].get('extraction_type', 'Unknown')}")
        print(f"📊 Files processed: {results['summary']['successful']}")
        print(f"❌ Files failed: {results['summary']['failed']}")
        
        # Show API usage if available
        if 'total_api_calls' in results['summary']:
            print(f"🔄 Total API calls: {results['summary']['total_api_calls']}")
            print(f"💰 Estimated cost: ~${results['summary']['total_api_calls'] * 0.50:.2f}")
        
        print(f"📁 Results saved to: {output_path}")
        
        # Show extraction stats
        total_constructs = 0
        total_assessments = 0
        total_interventions = 0
        
        for file_result in results['processed_files']:
            if 'error' not in file_result:
                total_constructs += file_result.get('constructs_identified', 0)
                if 'assessments' in file_result and file_result['assessments'].get('assessments'):
                    total_assessments += len(file_result['assessments']['assessments'])
                if 'interventions' in file_result and file_result['interventions'].get('interventions'):
                    total_interventions += len(file_result['interventions']['interventions'])
        
        print(f"🎯 Total constructs identified: {total_constructs}")
        print(f"🧪 Total assessments found: {total_assessments}")
        print(f"💊 Total interventions found: {total_interventions}")
        
        # Show robust data stats if available
        robust_entities = 0
        for file_result in results['processed_files']:
            if 'robust_data' in file_result and 'entities' in file_result['robust_data']:
                entities_data = file_result['robust_data']['entities']
                if isinstance(entities_data, dict):
                    for category in entities_data.values():
                        if isinstance(category, list):
                            robust_entities += len(category)
        
        if robust_entities > 0:
            print(f"🔍 Enhanced entities captured: {robust_entities}")
        
    except Exception as e:
        print(f"❌ Processing failed: {e}")
        import traceback
        traceback.print_exc()

def quick_test():
    """Quick test function for development"""
    print("🧪 QUICK TEST MODE")
    print("=" * 30)
    
    # Check for test file
    test_file = Path("tests/sample_transcript.txt")
    if not test_file.exists():
        print("❌ No test file found. Run the full pipeline instead.")
        return
    
    try:
        # Use robust extractor for testing
        extractor = RobustOntologyExtractor()
        result = extractor.process_single_transcript(test_file)
        
        print("\n📊 TEST RESULTS:")
        print(f"File: {result['file_name']}")
        print(f"Constructs identified: {result['constructs_identified']}")
        
        if 'robust_data' in result:
            print("✅ Robust extraction data available")
            
        print("🎉 Test completed successfully!")
        
    except Exception as e:
        print(f"❌ Test failed: {e}")

if __name__ == "__main__":
    # Check if running in test mode
    if len(sys.argv) > 1 and sys.argv[1] == "test":
        quick_test()
    else:
        main()