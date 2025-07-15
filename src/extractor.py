# src/extractor.py
import anthropic
import json
import os
from pathlib import Path
from typing import Dict, List
import sys

# Add project root to Python path for imports
project_root = Path(__file__).parent.parent
sys.path.append(str(project_root))

try:
    from dotenv import load_dotenv
    load_dotenv()
except ImportError:
    print("Note: python-dotenv not available. Make sure to set ANTHROPIC_API_KEY manually.")

from src.prompts import ExtractionPrompts
from config.ontology_schema import ONTOLOGY_SCHEMA

class OntologyExtractor:
    def __init__(self, api_key=None):
        # Get API key
        if api_key:
            self.api_key = api_key
        else:
            self.api_key = os.getenv('ANTHROPIC_API_KEY')
        
        if not self.api_key:
            raise ValueError("API key required. Either pass it directly or set ANTHROPIC_API_KEY environment variable")
        
        # Initialize Anthropic client
        self.client = anthropic.Anthropic(api_key=self.api_key)
        self.ontology_schema = ONTOLOGY_SCHEMA
        self.prompts = ExtractionPrompts()
        print("✅ Extractor initialized successfully")
        
    def make_api_call(self, prompt: str, max_tokens: int = 4000) -> str:
        """Make API call to Claude with error handling"""
        try:
            response = self.client.messages.create(
                model="claude-sonnet-4-20250514",
                max_tokens=max_tokens,
                messages=[{"role": "user", "content": prompt}]
            )
            return response.content[0].text
        except Exception as e:
            print(f"❌ API call failed: {e}")
            raise
    
    def safe_json_parse(self, text: str) -> Dict:
        """Safely parse JSON response with fallback"""
        try:
            # Remove markdown code blocks if present
            text = text.strip()
            if text.startswith('```json'):
                text = text[7:]  # Remove ```json
            if text.startswith('```'):
                text = text[3:]   # Remove ```
            if text.endswith('```'):
                text = text[:-3]  # Remove closing ```
            
            # Clean up any extra whitespace
            text = text.strip()
            
            return json.loads(text)
        except json.JSONDecodeError as e:
            print(f"⚠️ JSON parsing failed: {e}")
            print(f"Response preview: {text[:200]}...")
            return {"error": "JSON parsing failed", "raw_response": text}
    
    def extract_domains_constructs(self, transcript: str) -> Dict:
        """Extract domains and constructs mentioned in the interview"""
        print("  📋 Extracting domains and constructs...")
        prompt = self.prompts.domains_constructs_prompt(transcript)
        response_text = self.make_api_call(prompt)
        return self.safe_json_parse(response_text)
    
    def extract_assessments(self, transcript: str, constructs: List[str]) -> Dict:
        """Extract detailed assessment information"""
        print("  🧪 Extracting assessments...")
        prompt = self.prompts.assessments_prompt(transcript, constructs)
        response_text = self.make_api_call(prompt)
        return self.safe_json_parse(response_text)
    
    def extract_interventions(self, transcript: str, constructs: List[str]) -> Dict:
        """Extract intervention information and protocols"""
        print("  💊 Extracting interventions...")
        prompt = self.prompts.interventions_prompt(transcript, constructs)
        response_text = self.make_api_call(prompt)
        return self.safe_json_parse(response_text)
    
    def process_single_transcript(self, file_path: Path) -> Dict:
        """Process a single transcript file"""
        print(f"\n📄 Processing: {file_path.name}")
        
        # Read transcript
        with open(file_path, 'r', encoding='utf-8') as f:
            transcript = f.read()
        
        # Extract domains and constructs first
        domains_constructs = self.extract_domains_constructs(transcript)
        
        # Extract construct names for subsequent passes
        constructs_list = []
        if "constructs_mentioned" in domains_constructs and domains_constructs["constructs_mentioned"]:
            constructs_list = [c.get("construct_name", "") for c in domains_constructs["constructs_mentioned"] if c.get("construct_name")]
        
        # Extract assessments and interventions
        assessments = self.extract_assessments(transcript, constructs_list)
        interventions = self.extract_interventions(transcript, constructs_list)
        
        result = {
            "file_name": file_path.name,
            "transcript_length": len(transcript),
            "constructs_identified": len(constructs_list),
            "domains_constructs": domains_constructs,
            "assessments": assessments,
            "interventions": interventions
        }
        
        print(f"  ✅ Found {len(constructs_list)} constructs")
        return result
    
    def process_transcript_folder(self, folder_path: str) -> Dict:
        """Process all transcripts in a folder"""
        folder = Path(folder_path)
        if not folder.exists():
            raise ValueError(f"Folder does not exist: {folder_path}")
        
        # Find all .txt files
        transcript_files = list(folder.glob("*.txt"))
        if not transcript_files:
            print(f"❌ No .txt files found in {folder_path}")
            return {"error": "No transcript files found"}
        
        print(f"📁 Found {len(transcript_files)} transcript files")
        
        results = {
            "processed_files": [],
            "summary": {
                "total_files": len(transcript_files),
                "successful": 0,
                "failed": 0
            }
        }
        
        # Process each file
        for i, file_path in enumerate(transcript_files, 1):
            try:
                print(f"\n[{i}/{len(transcript_files)}]", end=" ")
                file_result = self.process_single_transcript(file_path)
                results["processed_files"].append(file_result)
                results["summary"]["successful"] += 1
                
            except Exception as e:
                print(f"❌ Error processing {file_path.name}: {e}")
                results["processed_files"].append({
                    "file_name": file_path.name,
                    "error": str(e)
                })
                results["summary"]["failed"] += 1
        
        return results
    
    def save_results(self, results: Dict, output_dir: str = "data/outputs"):
        """Save results to files"""
        output_path = Path(output_dir)
        output_path.mkdir(parents=True, exist_ok=True)
        
        # Save full results
        results_file = output_path / "extraction_results.json"
        with open(results_file, "w") as f:
            json.dump(results, f, indent=2)
        
        print(f"💾 Results saved to {results_file}")
        return output_path