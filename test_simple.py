# test_simple.py
"""
Simple test script to verify the pipeline works
Run this first before processing real transcripts
"""

import os
from pathlib import Path
import json

# Set up path for imports
import sys
project_root = Path(__file__).parent
sys.path.append(str(project_root))

from src.extractor import OntologyExtractor

def create_test_transcript():
    """Create a simple test transcript if it doesn't exist"""
    test_dir = Path("tests")
    test_dir.mkdir(exist_ok=True)
    
    test_file = test_dir / "sample_transcript.txt"
    
    if not test_file.exists():
        sample_content = """
Interviewer: What are your main areas of expertise?

Practitioner: I specialize primarily in cardiovascular health and performance optimization for endurance athletes. My main focus is on assessing and improving aerobic capacity, heart rate variability, and blood pressure control.

Interviewer: How do you typically assess cardiovascular health?

Practitioner: I use several key assessments. First, I do a graded exercise test using a treadmill with VO2 max measurement - that gives us peak oxygen uptake in ml/kg/min. I also use resting heart rate variability measurement with a Polar H10 chest strap.

For the VO2 max test, the protocol involves a 5-minute warm-up, then incremental increases every 2 minutes until exhaustion. Common mistakes include not following the breathing pattern or stopping too early.

The key metrics I look at are VO2 max, lactate threshold, and maximum heart rate. For athletes, I consider VO2 max above 60 ml/kg/min as excellent.

Interviewer: What interventions do you recommend?

Practitioner: For improving cardiovascular health, I primarily use periodized endurance training programs. These typically run 12-16 weeks with a mix of base training, threshold work, and high-intensity intervals. 

The program structure includes 3-4 training sessions per week, with progression based on heart rate zones. I use Garmin devices to monitor training load and recovery.
"""
        
        with open(test_file, 'w') as f:
            f.write(sample_content)
        print(f"✅ Created test transcript: {test_file}")
    
    return test_file

def test_pipeline():
    print("🧪 Testing Ontology Pipeline")
    print("=" * 40)
    
    # Check if API key is available
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
    
    try:
        # Initialize extractor
        extractor = OntologyExtractor(api_key=api_key)
        
        # Create test transcript if needed
        test_file = create_test_transcript()
        
        # Process the test file
        print(f"\n📄 Processing test file: {test_file}")
        result = extractor.process_single_transcript(test_file)
        
        # Show results
        print("\n📊 EXTRACTION RESULTS:")
        print(f"File: {result['file_name']}")
        print(f"Transcript length: {result['transcript_length']} characters")
        print(f"Constructs identified: {result['constructs_identified']}")
        
        # Show some extracted data
        if result['domains_constructs'].get('practitioner_domains'):
            print("\n🎯 Domains found:")
            for domain in result['domains_constructs']['practitioner_domains']:
                print(f"  - {domain.get('domain_name', 'Unknown')}")
        
        if result['assessments'].get('assessments'):
            print("\n🧪 Assessments found:")
            for assessment in result['assessments']['assessments']:
                print(f"  - {assessment.get('assessment_name', 'Unknown')}")
        
        # Save test results
        output_dir = Path("data/outputs")
        output_dir.mkdir(parents=True, exist_ok=True)
        
        with open(output_dir / "test_results.json", "w") as f:
            json.dump(result, f, indent=2)
        
        print(f"\n💾 Test results saved to: {output_dir / 'test_results.json'}")
        print("✅ TEST SUCCESSFUL!")
        
        return True
        
    except Exception as e:
        print(f"❌ Test failed: {e}")
        import traceback
        traceback.print_exc()
        return False

if __name__ == "__main__":
    success = test_pipeline()
    if success:
        print("\n🚀 Ready to process real transcripts!")
        print("Put your .txt files in data/transcripts/ and run main.py")