# main.py
"""
Main script with enhanced extractor selection including ontology-guided extraction
"""

import os
from pathlib import Path
import json
import sys

# Set up path for imports
project_root = Path(__file__).parent
sys.path.append(str(project_root))

from src.extractor import OntologyExtractor, RobustOntologyExtractor, OntologyGuidedExtractor

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
    
    # Enhanced extractor selection
    print("\n🔧 EXTRACTOR SELECTION:")
    print("1. Standard (4-pass) - Original extraction method")
    print("2. Robust (7-pass) - Enhanced comprehensive extraction")
    print("3. Ontology-Guided (8-pass) - Targeted extraction with ontology definitions")
    print("4. Auto-select based on file count")
    
    try:
        choice = input("\nChoose extractor (1/2/3/4) [default: 3]: ").strip()
        if not choice:
            choice = "3"
    except:
        choice = "3"  # Default for non-interactive environments
    
    # Initialize extractor based on choice
    try:
        if choice == "1":
            extractor = OntologyExtractor(api_key=api_key)
        elif choice == "2":
            extractor = RobustOntologyExtractor(api_key=api_key)
        elif choice == "4":
            # Auto-select based on file count
            transcript_folder = "data/transcripts"
            if Path(transcript_folder).exists():
                file_count = len(list(Path(transcript_folder).glob("*.txt")))
                if file_count <= 2:
                    print("📊 Auto-selecting Ontology-Guided extractor (≤2 files)")
                    extractor = OntologyGuidedExtractor(api_key=api_key)
                elif file_count <= 5:
                    print("📊 Auto-selecting Robust extractor (3-5 files)")
                    extractor = RobustOntologyExtractor(api_key=api_key)
                else:
                    print("📊 Auto-selecting Standard extractor (>5 files)")
                    extractor = OntologyExtractor(api_key=api_key)
            else:
                extractor = OntologyGuidedExtractor(api_key=api_key)
        else:  # Default to ontology-guided
            extractor = OntologyGuidedExtractor(api_key=api_key)
            
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
        print(f"🔧 Extractor used: {results['summary'].get('extraction_type', 'Unknown')}")
        print(f"📊 Files processed: {results['summary']['successful']}")
        print(f"❌ Files failed: {results['summary']['failed']}")
        
        # Show API usage if available
        if 'total_api_calls' in results['summary']:
            print(f"🔄 Total API calls: {results['summary']['total_api_calls']}")
            print(f"💰 Estimated cost: ~${results['summary']['total_api_calls'] * 0.50:.2f}")
        
        print(f"📁 Results saved to: {output_path}")
        
        # Enhanced extraction stats
        total_constructs = 0
        total_assessments = 0
        total_interventions = 0
        total_technologies = 0
        total_metrics = 0
        
        for file_result in results['processed_files']:
            if 'error' not in file_result:
                total_constructs += file_result.get('constructs_identified', 0)
                
                # Standard assessment/intervention counting
                if 'assessments' in file_result and file_result['assessments'].get('assessments'):
                    total_assessments += len(file_result['assessments']['assessments'])
                if 'interventions' in file_result and file_result['interventions'].get('interventions'):
                    total_interventions += len(file_result['interventions']['interventions'])
                
                # Enhanced ontology-guided counting
                if 'ontology_guided_data' in file_result:
                    og_data = file_result['ontology_guided_data']
                    if 'technologies_metrics' in og_data:
                        tm_data = og_data['technologies_metrics']
                        if 'technologies' in tm_data:
                            total_technologies += len(tm_data['technologies'])
                        if 'metrics' in tm_data:
                            total_metrics += len(tm_data['metrics'])
        
        print(f"🎯 Total constructs identified: {total_constructs}")
        print(f"🧪 Total assessments found: {total_assessments}")
        print(f"💊 Total interventions found: {total_interventions}")
        
        if total_technologies > 0 or total_metrics > 0:
            print(f"⚙️  Total technologies identified: {total_technologies}")
            print(f"📏 Total metrics catalogued: {total_metrics}")
        
        # Show detailed breakdown for ontology-guided extraction
        if hasattr(extractor, 'extraction_type') and 'Ontology-Guided' in extractor.extraction_type:
            print("\n📊 ONTOLOGY-GUIDED BREAKDOWN:")
            for file_result in results['processed_files']:
                if 'error' not in file_result and 'ontology_guided_data' in file_result:
                    print(f"  📄 {file_result['file_name']}:")
                    og_data = file_result['ontology_guided_data']
                    
                    # Technologies breakdown
                    if 'technologies_metrics' in og_data and 'technologies' in og_data['technologies_metrics']:
                        techs = og_data['technologies_metrics']['technologies']
                        if techs:
                            print(f"    ⚙️  Technologies: {[t.get('technology_name', 'Unknown') for t in techs[:3]]}")
                    
                    # Metrics breakdown
                    if 'technologies_metrics' in og_data and 'metrics' in og_data['technologies_metrics']:
                        metrics = og_data['technologies_metrics']['metrics']
                        if metrics:
                            print(f"    📏 Metrics: {[m.get('metric_name', 'Unknown') for m in metrics[:3]]}")
                    
                    # Validation confidence
                    if 'validation' in og_data and 'quality_assessment' in og_data['validation']:
                        qa = og_data['validation']['quality_assessment']
                        confidence = qa.get('overall_confidence', 'unknown')
                        print(f"    ✅ Extraction confidence: {confidence}")
        
        # Show any validation warnings
        validation_warnings = []
        for file_result in results['processed_files']:
            if ('ontology_guided_data' in file_result and 
                'validation' in file_result['ontology_guided_data'] and
                'potential_missed_entities' in file_result['ontology_guided_data']['validation']):
                
                missed = file_result['ontology_guided_data']['validation']['potential_missed_entities']
                if missed:
                    validation_warnings.extend(missed)
        
        if validation_warnings:
            print(f"\n⚠️  VALIDATION ALERTS: {len(validation_warnings)} potential missed entities detected")
            print("   Consider reviewing the extraction results for completeness")
        
    except Exception as e:
        print(f"❌ Processing failed: {e}")
        import traceback
        traceback.print_exc()

def diagnose_extraction_issues():
    """Diagnostic function to help identify extraction problems"""
    print("🔍 EXTRACTION DIAGNOSTICS")
    print("=" * 30)
    
    # Check for recent extraction results
    output_file = Path("data/outputs/extraction_results.json")
    if not output_file.exists():
        print("❌ No extraction results found. Run the pipeline first.")
        return
    
    with open(output_file, 'r') as f:
        results = json.load(f)
    
    print("📊 DIAGNOSTIC SUMMARY:")
    for file_result in results.get('processed_files', []):
        if 'error' not in file_result:
            file_name = file_result.get('file_name', 'Unknown')
            constructs = file_result.get('constructs_identified', 0)
            
            print(f"\n📄 {file_name}:")
            print(f"  Constructs: {constructs}")
            
            # Check for assessments
            assessments = file_result.get('assessments', {}).get('assessments', [])
            print(f"  Assessments: {len(assessments)}")
            if assessments:
                print(f"    Examples: {[a.get('assessment_name', 'Unknown')[:30] for a in assessments[:2]]}")
            
            # Check for technologies in ontology-guided data
            if 'ontology_guided_data' in file_result:
                og_data = file_result['ontology_guided_data']
                if 'technologies_metrics' in og_data:
                    techs = og_data['technologies_metrics'].get('technologies', [])
                    metrics = og_data['technologies_metrics'].get('metrics', [])
                    print(f"  Technologies: {len(techs)}")
                    print(f"  Metrics: {len(metrics)}")
                    
                    if techs:
                        print(f"    Tech examples: {[t.get('technology_name', 'Unknown')[:20] for t in techs[:2]]}")
                    if metrics:
                        print(f"    Metric examples: {[m.get('metric_name', 'Unknown')[:20] for m in metrics[:2]]}")
            
            # Check validation results
            if ('ontology_guided_data' in file_result and 
                'validation' in file_result['ontology_guided_data']):
                validation = file_result['ontology_guided_data']['validation']
                if 'ontology_coverage_check' in validation:
                    coverage = validation['ontology_coverage_check']
                    print(f"  Coverage check: Technologies={coverage.get('technologies_identified', 0)}, Metrics={coverage.get('metrics_identified', 0)}")

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
        # Use ontology-guided extractor for testing
        extractor = OntologyGuidedExtractor()
        result = extractor.process_single_transcript(test_file)
        
        print("\n📊 TEST RESULTS:")
        print(f"File: {result['file_name']}")
        print(f"Constructs identified: {result['constructs_identified']}")
        
        if 'ontology_guided_data' in result:
            og_data = result['ontology_guided_data']
            if 'technologies_metrics' in og_data:
                techs = len(og_data['technologies_metrics'].get('technologies', []))
                metrics = len(og_data['technologies_metrics'].get('metrics', []))
                print(f"Technologies found: {techs}")
                print(f"Metrics found: {metrics}")
        
        print("🎉 Test completed successfully!")
        
    except Exception as e:
        print(f"❌ Test failed: {e}")

if __name__ == "__main__":
    # Check command line arguments
    if len(sys.argv) > 1:
        if sys.argv[1] == "test":
            quick_test()
        elif sys.argv[1] == "diagnose":
            diagnose_extraction_issues()
        else:
            main()
    else:
        main()