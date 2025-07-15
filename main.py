# main.py
"""
Main script to process all transcripts in the data/transcripts folder
"""

import os
from pathlib import Path
import json
import sys

# Set up path for imports
project_root = Path(__file__).parent
sys.path.append(str(project_root))

from src.extractor import OntologyExtractor

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
    
    # Initialize extractor
    try:
        extractor = OntologyExtractor(api_key=api_key)
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
        
        # Print summary
        print("\n" + "=" * 50)
        print("✅ EXTRACTION COMPLETE!")
        print(f"📊 Files processed: {results['summary']['successful']}")
        print(f"❌ Files failed: {results['summary']['failed']}")
        print(f"📁 Results saved to: {output_path}")
        
        # Show some stats
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
        
    except Exception as e:
        print(f"❌ Processing failed: {e}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    main()