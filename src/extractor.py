# src/extractor.py
"""
Unified extraction system with multiple extractor options
Integrates with improved centralized prompts system
"""

import anthropic
import json
import os
from pathlib import Path
from typing import Dict, List, Optional
import sys
import time

# Add project root to Python path for imports
project_root = Path(__file__).parent.parent
sys.path.append(str(project_root))

try:
    from dotenv import load_dotenv
    load_dotenv()
except ImportError:
    print("Note: python-dotenv not available. Make sure to set ANTHROPIC_API_KEY manually.")

from src.prompts import OntologyPrompts, ExtractionPrompts  # Import both for compatibility
from config.ontology_schema import ONTOLOGY_SCHEMA

class BaseOntologyExtractor:
    """Base class with shared functionality"""
    
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
        self.prompts = OntologyPrompts()  # Use new improved prompts
        
    def load_existing_results(self, output_dir: str = "data/outputs") -> Dict:
        """Load existing extraction results if they exist"""
        output_path = Path(output_dir)
        results_file = output_path / "extraction_results.json"
        
        if results_file.exists():
            try:
                with open(results_file, 'r') as f:
                    existing_results = json.load(f)
                print(f"📂 Loaded existing results with {len(existing_results.get('processed_files', []))} files")
                return existing_results
            except Exception as e:
                print(f"⚠️ Failed to load existing results: {e}")
        
        return None
    

    
    def get_processed_filenames(self, existing_results: Dict) -> set:
        """Get set of already processed filenames"""
        if not existing_results or 'processed_files' not in existing_results:
            return set()
        
        processed_files = set()
        for file_result in existing_results.get('processed_files', []):
            if 'error' not in file_result:
                processed_files.add(file_result['file_name'])
        
        return processed_files
    
    def merge_results(self, existing_results: Dict, new_results: Dict) -> Dict:
        """Merge new results with existing results"""
        if not existing_results:
            return new_results
        
        # Create a map of existing results by filename
        existing_map = {}
        for file_result in existing_results.get('processed_files', []):
            if 'error' not in file_result:
                existing_map[file_result['file_name']] = file_result
        
        # Add new results, overwriting any duplicates
        for file_result in new_results.get('processed_files', []):
            if 'error' not in file_result:
                existing_map[file_result['file_name']] = file_result
        
        # Rebuild the merged results
        merged_results = {
            "processed_files": list(existing_map.values()),
            "summary": {
                "total_files": len(existing_map),
                "successful": len([f for f in existing_map.values() if 'error' not in f]),
                "failed": len([f for f in existing_map.values() if 'error' in f]),
                "extraction_type": new_results['summary'].get('extraction_type', existing_results['summary'].get('extraction_type', 'Unknown')),
                "total_api_calls": existing_results['summary'].get('total_api_calls', 0) + new_results['summary'].get('total_api_calls', 0)
            }
        }
        
        return merged_results
        
    def make_api_call(self, prompt: str, max_tokens: int = 4000) -> str:
        """Make API call to Claude with error handling"""
        try:
            response = self.client.messages.create(
                model="claude-sonnet-4-20250514",
                max_tokens=max_tokens,
                messages=[{"role": "user", "content": prompt}],
                temperature=0.1
            )
            return response.content[0].text
        except Exception as e:
            print(f"❌ API call failed: {e}")
            raise
    
    def safe_json_parse(self, text: str) -> Dict:
        """Safely parse JSON response with fallback"""
        try:
            cleaned_text = self.clean_response_text(text)
            return json.loads(cleaned_text)
        except json.JSONDecodeError as e:
            print(f"⚠️ JSON parsing failed: {e}")
            print(f"Response preview: {cleaned_text[:200]}...")
            return {"error": "JSON parsing failed", "raw_response": text}
    
    def clean_response_text(self, text: str) -> str:
        """Enhanced JSON cleaning"""
        text = text.strip()
        
        # Remove any text before JSON
        json_start = text.find('{')
        if json_start > 0:
            text = text[json_start:]
        
        # Remove markdown blocks
        if text.startswith('```json'):
            text = text[7:]
        elif text.startswith('```'):
            text = text[3:]
        
        if text.endswith('```'):
            text = text[:-3]
        
        # Find the actual JSON object
        json_start = text.find('{')
        json_end = text.rfind('}')
        
        if json_start != -1 and json_end != -1 and json_end > json_start:
            text = text[json_start:json_end + 1]
        
        return text.strip()
    
    def save_results(self, results: Dict, output_dir: str = "data/outputs"):
        """Save results to files"""
        output_path = Path(output_dir)
        output_path.mkdir(parents=True, exist_ok=True)
        
        # Save full results
        with open(output_path / "extraction_results.json", "w") as f:
            json.dump(results, f, indent=2)
        
        print(f"💾 Results saved to {output_path}")
        return output_path

class OntologyExtractor(BaseOntologyExtractor):
    """Enhanced standard 4-pass extraction system with improved prompts"""
    
    def __init__(self, api_key=None):
        super().__init__(api_key)
        self.extraction_type = "Enhanced Standard (4-pass)"
        print("✅ Enhanced Standard Extractor initialized successfully")
        print("🔄 Using 4-pass extraction with improved prompts")
    
    def extract_domains_constructs(self, transcript: str) -> Dict:
        """Extract domains and constructs using enhanced prompts"""
        prompt = self.prompts.domains_constructs_standard(transcript)
        response_text = self.make_api_call(prompt)
        return self.safe_json_parse(response_text)
    
    def extract_assessments(self, transcript: str, constructs: List[str]) -> Dict:
        """Extract detailed assessment information using enhanced prompts"""
        prompt = self.prompts.assessments_standard(transcript, constructs)
        response_text = self.make_api_call(prompt)
        return self.safe_json_parse(response_text)
    
    def extract_interventions(self, transcript: str, constructs: List[str]) -> Dict:
        """Extract intervention information using enhanced prompts"""
        prompt = self.prompts.interventions_standard(transcript, constructs)
        response_text = self.make_api_call(prompt)
        return self.safe_json_parse(response_text)
    
    def extract_relationships(self, transcript: str, all_entities: Dict) -> Dict:
        """Extract construct relationships and dependencies"""
        prompt = self.prompts.relationships_standard(transcript, all_entities)
        response_text = self.make_api_call(prompt)
        return self.safe_json_parse(response_text)
    
    def process_single_transcript(self, file_path: Path) -> Dict:
        """Process a single transcript file using enhanced standard approach"""
        print(f"📄 Processing: {file_path.name}")
        
        with open(file_path, 'r', encoding='utf-8') as f:
            transcript = f.read()
        
        # 4-pass extraction with enhanced prompts
        print("  📋 Extracting domains and constructs...")
        domains_constructs = self.extract_domains_constructs(transcript)
        
        constructs_list = []
        if "constructs_mentioned" in domains_constructs:
            constructs_list = [c.get("construct_name", "") for c in domains_constructs["constructs_mentioned"]]
        
        print("  🧪 Extracting assessments...")
        assessments = self.extract_assessments(transcript, constructs_list)
        
        print("  💊 Extracting interventions...")
        interventions = self.extract_interventions(transcript, constructs_list)
        
        all_entities = {
            "domains_constructs": domains_constructs,
            "assessments": assessments,
            "interventions": interventions
        }
        
        print("  🔗 Extracting relationships...")
        relationships = self.extract_relationships(transcript, all_entities)
        
        result = {
            "file_name": file_path.name,
            "transcript_length": len(transcript),
            "constructs_identified": len(constructs_list),
            "domains_constructs": domains_constructs,
            "assessments": assessments,
            "interventions": interventions,
            "relationships": relationships
        }
        
        print(f"  ✅ Found {len(constructs_list)} constructs")
        return result
    
    def process_transcript_folder(self, folder_path: str) -> Dict:
        """Process all transcripts using enhanced standard approach with incremental processing"""
        folder = Path(folder_path)
        if not folder.exists():
            raise ValueError(f"Folder does not exist: {folder_path}")
        
        # Load existing results
        existing_results = self.load_existing_results()
        processed_filenames = self.get_processed_filenames(existing_results)
        
        transcript_files = list(folder.glob("*.txt"))
        if not transcript_files:
            print(f"❌ No .txt files found in {folder_path}")
            return existing_results or {"error": "No transcript files found"}
        
        # Filter for only new/unprocessed files
        new_files = [f for f in transcript_files if f.name not in processed_filenames]
        already_processed = [f for f in transcript_files if f.name in processed_filenames]
        
        print(f"📁 Found {len(transcript_files)} total transcript files")
        print(f"✅ Already processed: {len(already_processed)} files")
        print(f"🆕 New files to process: {len(new_files)} files")
        
        if not new_files:
            print("🎉 All transcripts already processed!")
            return existing_results
        
        # Process only new files
        new_results = {
            "processed_files": [],
            "summary": {
                "total_files": len(new_files),
                "successful": 0,
                "failed": 0,
                "extraction_type": self.extraction_type,
                "total_api_calls": 0
            }
        }
        
        for i, file_path in enumerate(new_files, 1):
            try:
                print(f"\n[{i}/{len(new_files)}] Processing new file: {file_path.name}")
                file_result = self.process_single_transcript(file_path)
                new_results["processed_files"].append(file_result)
                new_results["summary"]["successful"] += 1
                new_results["summary"]["total_api_calls"] += 4  # 4 passes
                
                # Small delay for API rate limiting
                time.sleep(0.5)
                
            except Exception as e:
                print(f"❌ Error processing {file_path.name}: {e}")
                new_results["processed_files"].append({
                    "file_name": file_path.name,
                    "error": str(e)
                })
                new_results["summary"]["failed"] += 1
        
        # Merge with existing results
        final_results = self.merge_results(existing_results, new_results)
        
        print(f"\n📊 MERGE SUMMARY:")
        print(f"   Existing files preserved: {len(already_processed)}")
        print(f"   New files processed: {len(new_files)}")
        print(f"   Total files in results: {final_results['summary']['total_files']}")
        print(f"   New API calls made: {new_results['summary']['total_api_calls']}")
        print(f"   Total API calls (all time): {final_results['summary']['total_api_calls']}")
        
        return final_results

class RobustOntologyExtractor(BaseOntologyExtractor):
    """Enhanced 7-pass extraction system for maximum information capture"""
    
    def __init__(self, api_key=None):
        super().__init__(api_key)
        self.extraction_type = "Robust (7-pass)"
        print("✅ Robust Extractor initialized successfully")
        print("🔄 Using 7-pass robust extraction strategy")
    
    def extract_knowledge_domains(self, transcript: str) -> Dict:
        """Pass 1: Open-ended knowledge domain mapping"""
        prompt = self.prompts.knowledge_mapping_guided(transcript)
        response = self.make_api_call(prompt, max_tokens=4000)
        return self.safe_json_parse(response)
    
    def extract_comprehensive_entities(self, transcript: str, knowledge_map: Dict) -> Dict:
        """Pass 2: Comprehensive entity extraction"""
        expertise_context = ""
        if knowledge_map and "primary_expertise" in knowledge_map:
            expertise_areas = [area.get("area", "") for area in knowledge_map["primary_expertise"]]
            expertise_context = f"Primary expertise: {', '.join(expertise_areas)}"
        
        prompt = self.prompts.constructs_guided(transcript, expertise_context)
        response = self.make_api_call(prompt, max_tokens=4000)
        return self.safe_json_parse(response)
    
    def extract_detailed_assessments(self, transcript: str, entities: Dict) -> Dict:
        """Pass 3: Detailed assessment extraction"""
        constructs_list = []
        if entities and "constructs_mentioned" in entities:
            constructs_list = [c.get("construct_name", "") for c in entities["constructs_mentioned"]]
        
        prompt = self.prompts.assessments_guided(transcript, constructs_list)
        response = self.make_api_call(prompt, max_tokens=4000)
        return self.safe_json_parse(response)
    
    def extract_detailed_interventions(self, transcript: str, entities: Dict) -> Dict:
        """Pass 4: Detailed intervention extraction"""
        constructs_list = []
        if entities and "constructs_mentioned" in entities:
            constructs_list = [c.get("construct_name", "") for c in entities["constructs_mentioned"]]
        
        prompt = self.prompts.interventions_guided(transcript, constructs_list)
        response = self.make_api_call(prompt, max_tokens=4000)
        return self.safe_json_parse(response)
    
    def extract_contextual_factors(self, transcript: str, entities: Dict) -> Dict:
        """Pass 5: Goals, constraints, and contextual factors"""
        prompt = f"""
        Extract all contextual information that affects assessment and intervention decisions.

        TRANSCRIPT:
        {transcript}

        Extract contextual factors:
        {{
            "client_goals": [
                {{
                    "goal_description": "string",
                    "goal_type": "string",
                    "target_metrics": ["specific measurable outcomes"],
                    "timeline": "string"
                }}
            ],
            "constraints_and_limitations": [
                {{
                    "constraint_type": "string",
                    "description": "string",
                    "impact_on_assessment": "string",
                    "impact_on_intervention": "string",
                    "workaround_strategies": ["accommodations"]
                }}
            ],
            "moderating_factors": [
                {{
                    "factor_name": "string",
                    "description": "string",
                    "what_it_moderates": "string",
                    "management_strategies": ["how to account for this factor"]
                }}
            ]
        }}
        """
        
        response = self.make_api_call(prompt, max_tokens=4000)
        return self.safe_json_parse(response)
    
    def extract_comprehensive_relationships(self, transcript: str, all_data: Dict) -> Dict:
        """Pass 6: Comprehensive relationship extraction"""
        prompt = f"""
        Analyze this interview for ALL types of relationships, dependencies, and connections discussed.

        TRANSCRIPT:
        {transcript}

        Extract all relationship types:
        {{
            "causal_relationships": [
                {{
                    "cause": "string",
                    "effect": "string",
                    "relationship_strength": "string",
                    "mechanism": "string",
                    "evidence_mentioned": "string"
                }}
            ],
            "assessment_construct_links": [
                {{
                    "assessment": "string",
                    "constructs_measured": ["list"],
                    "measurement_quality": "string"
                }}
            ],
            "intervention_outcome_links": [
                {{
                    "intervention": "string",
                    "target_outcomes": ["list"],
                    "expected_timeline": "string",
                    "moderating_factors": ["what affects effectiveness"]
                }}
            ]
        }}
        """
        
        response = self.make_api_call(prompt, max_tokens=4000)
        return self.safe_json_parse(response)
    
    def validate_and_enhance(self, transcript: str, all_extractions: Dict) -> Dict:
        """Pass 7: Validation and enhancement"""
        prompt = f"""
        Review this transcript and the extracted information to identify any significant gaps.

        TRANSCRIPT EXCERPT:
        {transcript[:2000]}...

        Provide validation:
        {{
            "extraction_confidence": {{
                "overall_confidence": "high/medium/low",
                "most_reliable_sections": ["list"],
                "areas_needing_review": ["list"]
            }},
            "missing_information": [
                {{
                    "category": "string",
                    "missing_element": "string",
                    "importance_level": "high/medium/low"
                }}
            ],
            "quality_indicators": [
                {{
                    "aspect": "string",
                    "quality_score": "high/medium/low",
                    "reasoning": "string"
                }}
            ]
        }}
        """
        
        response = self.make_api_call(prompt, max_tokens=3000)
        return self.safe_json_parse(response)
    
    def process_single_transcript(self, file_path: Path) -> Dict:
        """Process transcript with 7-pass robust extraction"""
        print(f"📄 Processing: {file_path.name}")
        
        with open(file_path, 'r', encoding='utf-8') as f:
            transcript = f.read()
        
        # 7-pass robust extraction
        print("  🗺️  Pass 1: Knowledge domain mapping...")
        knowledge_map = self.extract_knowledge_domains(transcript)
        
        print("  🔍 Pass 2: Comprehensive entity extraction...")
        entities = self.extract_comprehensive_entities(transcript, knowledge_map)
        
        print("  🧪 Pass 3: Detailed assessment extraction...")
        assessments = self.extract_detailed_assessments(transcript, entities)
        
        print("  💊 Pass 4: Detailed intervention extraction...")
        interventions = self.extract_detailed_interventions(transcript, entities)
        
        print("  🎯 Pass 5: Contextual factors extraction...")
        contextual_factors = self.extract_contextual_factors(transcript, entities)
        
        print("  🔗 Pass 6: Comprehensive relationship extraction...")
        all_data = {
            "knowledge_map": knowledge_map,
            "entities": entities,
            "assessments": assessments,
            "interventions": interventions,
            "contextual_factors": contextual_factors
        }
        relationships = self.extract_comprehensive_relationships(transcript, all_data)
        
        print("  ✅ Pass 7: Validation and enhancement...")
        validation = self.validate_and_enhance(transcript, all_data)
        
        # Extract construct names for summary
        constructs_list = []
        if entities and "constructs_mentioned" in entities:
            constructs_list = [c.get("construct_name", "") for c in entities["constructs_mentioned"]]
        
        result = {
            "file_name": file_path.name,
            "transcript_length": len(transcript),
            "constructs_identified": len(constructs_list),
            "knowledge_map": knowledge_map,
            "entities": entities,
            "assessments": assessments,
            "interventions": interventions,
            "contextual_factors": contextual_factors,
            "relationships": relationships,
            "validation": validation
        }
        
        print(f"  ✅ Found {len(constructs_list)} constructs")
        return result
    
    def process_transcript_folder(self, folder_path: str) -> Dict:
        """Process all transcripts using 7-pass robust extraction with incremental processing"""
        folder = Path(folder_path)
        if not folder.exists():
            raise ValueError(f"Folder does not exist: {folder_path}")
        
        # Load existing results
        existing_results = self.load_existing_results()
        processed_filenames = self.get_processed_filenames(existing_results)
        
        transcript_files = list(folder.glob("*.txt"))
        if not transcript_files:
            print(f"❌ No .txt files found in {folder_path}")
            return existing_results or {"error": "No transcript files found"}
        
        # Filter for only new/unprocessed files
        new_files = [f for f in transcript_files if f.name not in processed_filenames]
        already_processed = [f for f in transcript_files if f.name in processed_filenames]
        
        print(f"📁 Found {len(transcript_files)} total transcript files")
        print(f"✅ Already processed: {len(already_processed)} files")
        print(f"🆕 New files to process: {len(new_files)} files")
        
        if not new_files:
            print("🎉 All transcripts already processed!")
            return existing_results
        
        # Process only new files
        new_results = {
            "processed_files": [],
            "summary": {
                "total_files": len(new_files),
                "successful": 0,
                "failed": 0,
                "extraction_type": self.extraction_type,
                "total_api_calls": 0
            }
        }
        
        for i, file_path in enumerate(new_files, 1):
            try:
                print(f"\n[{i}/{len(new_files)}] Processing new file: {file_path.name}")
                file_result = self.process_single_transcript(file_path)
                new_results["processed_files"].append(file_result)
                new_results["summary"]["successful"] += 1
                new_results["summary"]["total_api_calls"] += 7  # 7 passes
                
                # Small delay for API rate limiting
                time.sleep(1)
                
            except Exception as e:
                print(f"❌ Error processing {file_path.name}: {e}")
                new_results["processed_files"].append({
                    "file_name": file_path.name,
                    "error": str(e)
                })
                new_results["summary"]["failed"] += 1
        
        # Merge with existing results
        final_results = self.merge_results(existing_results, new_results)
        
        print(f"\n📊 MERGE SUMMARY:")
        print(f"   Existing files preserved: {len(already_processed)}")
        print(f"   New files processed: {len(new_files)}")
        print(f"   Total files in results: {final_results['summary']['total_files']}")
        print(f"   New API calls made: {new_results['summary']['total_api_calls']}")
        print(f"   Total API calls (all time): {final_results['summary']['total_api_calls']}")
        
        return final_results

class OntologyGuidedExtractor(BaseOntologyExtractor):
    """Ontology-guided extraction that combines comprehensive coverage with specific term hunting"""
    
    def __init__(self, api_key=None):
        super().__init__(api_key)
        self.extraction_type = "Ontology-Guided (8-pass)"
        print("✅ Ontology-Guided Extractor initialized successfully")
        print("🔄 Using 8-pass ontology-guided extraction strategy")
    
    def extract_domains_constructs_guided(self, transcript: str) -> Dict:
        """Pass 1: Ontology-guided domain and construct extraction"""
        prompt = self.prompts.domains_constructs_standard(transcript)
        response_text = self.make_api_call(prompt, max_tokens=4000)
        return self.safe_json_parse(response_text)
    
    def extract_technologies_metrics_guided(self, transcript: str, assessments: List[str]) -> Dict:
        """Pass 3: Fixed technology and metrics extraction"""
        # Use the fixed prompt method
        prompt = self.prompts.technologies_metrics_guided_fixed(transcript, assessments)
        response = self.make_api_call(prompt, max_tokens=3000)  # Reduced tokens
        return self.safe_json_parse(response)
    
    def extract_assessments_guided(self, transcript: str, constructs: List[str]) -> Dict:
        """Pass 2: Fixed assessment extraction"""
        prompt = self.prompts.assessments_guided_fixed(transcript, constructs)
        response = self.make_api_call(prompt, max_tokens=3000)
        return self.safe_json_parse(response)
    
    def extract_interventions_guided(self, transcript: str, constructs: List[str]) -> Dict:
        """Pass 4: Fixed intervention extraction"""
        prompt = self.prompts.interventions_guided_fixed(transcript, constructs)
        response = self.make_api_call(prompt, max_tokens=3000)
        return self.safe_json_parse(response)
    
    def extract_goals_constraints_guided(self, transcript: str, constructs: List[str]) -> Dict:
        """Pass 5: Goals, constraints, and contextual factors"""
        prompt = f"""
        Extract goals, constraints, and contextual factors that affect practice decisions.

        CONSTRUCTS CONTEXT: {", ".join(constructs[:10])}

        TRANSCRIPT:
        {transcript}

        Extract contextual information:
        {{
            "client_goals": [
                {{
                    "goal_description": "string (specific goal mentioned)",
                    "goal_type": "string (performance/health/aesthetic/functional)",
                    "target_constructs": ["which constructs this goal relates to"],
                    "success_metrics": ["how success is measured"],
                    "timeline": "string (timeframe mentioned)",
                    "priority_level": "string (if indicated)"
                }}
            ],
            "constraints_preferences": [
                {{
                    "constraint_type": "string (equipment/time/access/medical/preference)",
                    "description": "string",
                    "impact_on_assessment": "string (how it affects testing)",
                    "impact_on_intervention": "string (how it affects treatment)",
                    "workaround_strategies": ["how to accommodate this constraint"]
                }}
            ],
            "moderating_factors": [
                {{
                    "factor_name": "string",
                    "description": "string",
                    "what_it_affects": "string (assessment results/intervention effectiveness)",
                    "management_approach": "string (how to account for this factor)"
                }}
            ],
            "individual_differences": [
                {{
                    "difference_factor": "string (age/sex/training status/health condition)",
                    "assessment_implications": "string",
                    "intervention_implications": "string"
                }}
            ]
        }}
        """
        
        response = self.make_api_call(prompt, max_tokens=4000)
        return self.safe_json_parse(response)
    
    def extract_relationships_guided(self, transcript: str, all_entities: Dict) -> Dict:
        """Pass 6: Comprehensive relationship extraction"""
        # Build context from extracted entities
        constructs = []
        assessments = []
        interventions = []
        
        if all_entities.get('constructs'):
            constructs = [c.get('construct_name', '') for c in all_entities['constructs'].get('constructs_mentioned', [])]
        if all_entities.get('assessments'):
            assessments = [a.get('assessment_name', '') for a in all_entities['assessments'].get('assessments', [])]
        if all_entities.get('interventions'):
            interventions = [i.get('intervention_name', '') for i in all_entities['interventions'].get('interventions', [])]
        
        context = f"""
        CONSTRUCTS: {", ".join(constructs[:10])}
        ASSESSMENTS: {", ".join(assessments[:10])}
        INTERVENTIONS: {", ".join(interventions[:10])}
        """
        
        prompt = f"""
        Analyze this interview for relationships between the entities identified:
        
        {context}

        TRANSCRIPT:
        {transcript}

        Extract all relationships mentioned:
        {{
            "construct_relationships": [
                {{
                    "source_construct": "string",
                    "target_construct": "string",
                    "relationship_type": "string (causal/association/dependency)",
                    "relationship_description": "string",
                    "evidence_mentioned": "string (what supports this relationship)",
                    "directionality": "string (bidirectional/unidirectional)"
                }}
            ],
            "assessment_construct_links": [
                {{
                    "assessment_name": "string",
                    "constructs_measured": ["list of constructs this assessment evaluates"],
                    "measurement_relationship": "string (direct/indirect/predictive)",
                    "interpretation_factors": ["what affects how results are interpreted"]
                }}
            ],
            "intervention_construct_links": [
                {{
                    "intervention_name": "string",
                    "constructs_targeted": ["list of constructs this intervention affects"],
                    "mechanism_of_action": "string (how the intervention works)",
                    "expected_outcomes": ["what changes are expected"],
                    "timeline_expectations": "string (how quickly effects are seen)"
                }}
            ],
            "assessment_intervention_connections": [
                {{
                    "assessment_name": "string",
                    "intervention_name": "string",
                    "connection_type": "string (informs/monitors/triggers/evaluates)",
                    "connection_description": "string"
                }}
            ]
        }}
        """
        
        response = self.make_api_call(prompt, max_tokens=4000)
        return self.safe_json_parse(response)
    
    def extract_protocols_details(self, transcript: str, assessments: List[str], interventions: List[str]) -> Dict:
        """Pass 7: Detailed protocols and implementation specifics"""
        
        prompt = f"""
        Extract detailed protocols and implementation specifics for the assessments and interventions identified.

        ASSESSMENTS: {", ".join(assessments[:10])}
        INTERVENTIONS: {", ".join(interventions[:10])}

        TRANSCRIPT:
        {transcript}

        Extract detailed protocols:
        {{
            "assessment_protocols": [
                {{
                    "assessment_name": "string",
                    "detailed_steps": ["ordered list of protocol steps"],
                    "preparation_requirements": ["what needs to be done before"],
                    "equipment_setup": "string",
                    "data_collection_process": "string",
                    "quality_assurance": ["how to ensure reliable results"],
                    "troubleshooting": ["common issues and solutions"]
                }}
            ],
            "intervention_protocols": [
                {{
                    "intervention_name": "string",
                    "implementation_steps": ["how to deliver this intervention"],
                    "dosage_specifications": {{
                        "specific_parameters": "string",
                        "progression_rules": "string",
                        "modification_criteria": "string"
                    }},
                    "monitoring_protocols": ["how to track progress"],
                    "safety_considerations": ["precautions and contraindications"]
                }}
            ],
            "practical_considerations": [
                {{
                    "consideration_type": "string",
                    "description": "string",
                    "practical_solutions": ["how to address this consideration"]
                }}
            ]
        }}
        """
        
        response = self.make_api_call(prompt, max_tokens=4000)
        return self.safe_json_parse(response)
    
    def validate_ontology_coverage(self, transcript: str, all_extractions: Dict) -> Dict:
        """Pass 8: Validation against ontology framework and gap identification"""
        prompt = self.prompts.validation_guided(transcript, all_extractions)
        response = self.make_api_call(prompt, max_tokens=3000)
        return self.safe_json_parse(response)
    
    def process_single_transcript(self, file_path: Path) -> Dict:
        """Process transcript with 8-pass ontology-guided extraction"""
        print(f"📄 Processing: {file_path.name}")
        
        with open(file_path, 'r', encoding='utf-8') as f:
            transcript = f.read()
        
        # Pass 1: Guided domain and construct extraction
        print("  🎯 Pass 1: Guided domains and constructs extraction...")
        domains_constructs = self.extract_domains_constructs_guided(transcript)
        
        # Extract construct names for subsequent passes
        constructs_list = []
        if domains_constructs and "constructs_mentioned" in domains_constructs:
            constructs_list = [c.get("construct_name", "") for c in domains_constructs["constructs_mentioned"]]
        
        # Pass 2: Guided assessment extraction
        print("  🧪 Pass 2: Guided assessments extraction...")
        assessments = self.extract_assessments_guided(transcript, constructs_list)
        
        # Extract assessment names
        assessment_names = []
        if assessments and "assessments" in assessments:
            assessment_names = [a.get("assessment_name", "") for a in assessments["assessments"]]
        
        # Pass 3: Dedicated technology and metrics extraction
        print("  ⚙️  Pass 3: Technologies and metrics extraction...")
        technologies_metrics = self.extract_technologies_metrics_guided(transcript, assessment_names)
        
        # Pass 4: Guided intervention extraction
        print("  💊 Pass 4: Guided interventions extraction...")
        interventions = self.extract_interventions_guided(transcript, constructs_list)
        
        # Extract intervention names
        intervention_names = []
        if interventions and "interventions" in interventions:
            intervention_names = [i.get("intervention_name", "") for i in interventions["interventions"]]
        
        # Pass 5: Goals and constraints
        print("  🎯 Pass 5: Goals and constraints extraction...")
        goals_constraints = self.extract_goals_constraints_guided(transcript, constructs_list)
        
        # Pass 6: Relationships
        print("  🔗 Pass 6: Relationships extraction...")
        all_entities = {
            'constructs': domains_constructs,
            'assessments': assessments,
            'interventions': interventions,
            'technologies': technologies_metrics
        }
        relationships = self.extract_relationships_guided(transcript, all_entities)
        
        # Pass 7: Detailed protocols
        print("  📋 Pass 7: Detailed protocols extraction...")
        protocols = self.extract_protocols_details(transcript, assessment_names, intervention_names)
        
        # Pass 8: Validation
        print("  ✅ Pass 8: Ontology validation...")
        all_extractions = {
            'constructs': domains_constructs,
            'assessments': assessments,
            'interventions': interventions,
            'technologies': technologies_metrics,
            'goals_constraints': goals_constraints,
            'relationships': relationships,
            'protocols': protocols
        }
        validation = self.validate_ontology_coverage(transcript, all_extractions)
        
        # Calculate summary stats
        total_constructs = len(constructs_list)
        total_assessments = len(assessment_names)
        total_interventions = len(intervention_names)
        total_technologies = len(technologies_metrics.get('technologies', []))
        total_metrics = len(technologies_metrics.get('metrics', []))
        
        result = {
            "file_name": file_path.name,
            "transcript_length": len(transcript),
            "constructs_identified": total_constructs,
            
            # Legacy format for compatibility
            "domains_constructs": domains_constructs,
            "assessments": assessments,
            "interventions": interventions,
            "relationships": relationships,
            
            # Enhanced ontology-guided data
            "ontology_guided_data": {
                "technologies_metrics": technologies_metrics,
                "goals_constraints": goals_constraints,
                "detailed_protocols": protocols,
                "validation": validation
            }
        }
        
        print(f"  ✅ Found: {total_constructs} constructs, {total_assessments} assessments, {total_interventions} interventions")
        print(f"     Technologies: {total_technologies}, Metrics: {total_metrics}")
        return result
    
    def process_transcript_folder(self, folder_path: str) -> Dict:
        """Process all transcripts using ontology-guided extraction with incremental processing"""
        folder = Path(folder_path)
        if not folder.exists():
            raise ValueError(f"Folder does not exist: {folder_path}")
        
        # Load existing results
        existing_results = self.load_existing_results()
        processed_filenames = self.get_processed_filenames(existing_results)
        
        transcript_files = list(folder.glob("*.txt"))
        if not transcript_files:
            print(f"❌ No .txt files found in {folder_path}")
            return existing_results or {"error": "No transcript files found"}
        
        # Filter for only new/unprocessed files
        new_files = [f for f in transcript_files if f.name not in processed_filenames]
        already_processed = [f for f in transcript_files if f.name in processed_filenames]
        
        print(f"📁 Found {len(transcript_files)} total transcript files")
        print(f"✅ Already processed: {len(already_processed)} files")
        print(f"🆕 New files to process: {len(new_files)} files")
        
        if not new_files:
            print("🎉 All transcripts already processed!")
            return existing_results
        
        # Process only new files
        new_results = {
            "processed_files": [],
            "summary": {
                "total_files": len(new_files),
                "successful": 0,
                "failed": 0,
                "extraction_type": self.extraction_type,
                "total_api_calls": 0
            }
        }
        
        for i, file_path in enumerate(new_files, 1):
            try:
                print(f"\n[{i}/{len(new_files)}] Processing new file: {file_path.name}")
                file_result = self.process_single_transcript(file_path)
                new_results["processed_files"].append(file_result)
                new_results["summary"]["successful"] += 1
                new_results["summary"]["total_api_calls"] += 8  # 8 passes
                
                # Small delay for API rate limiting
                time.sleep(1)
                
            except Exception as e:
                print(f"❌ Error processing {file_path.name}: {e}")
                new_results["processed_files"].append({
                    "file_name": file_path.name,
                    "error": str(e)
                })
                new_results["summary"]["failed"] += 1
        
        # Merge with existing results
        final_results = self.merge_results(existing_results, new_results)
        
        print(f"\n📊 MERGE SUMMARY:")
        print(f"   Existing files preserved: {len(already_processed)}")
        print(f"   New files processed: {len(new_files)}")
        print(f"   Total files in results: {final_results['summary']['total_files']}")
        print(f"   New API calls made: {new_results['summary']['total_api_calls']}")
        print(f"   Total API calls (all time): {final_results['summary']['total_api_calls']}")
        
        return final_results

# Factory function for easy extractor selection
def create_extractor(extractor_type: str = "standard", api_key: Optional[str] = None):
    """
    Factory function to create the appropriate extractor
    
    Args:
        extractor_type: "standard" for 4-pass, "robust" for 7-pass, or "guided" for 8-pass ontology-guided
        api_key: Optional API key
    
    Returns:
        Configured extractor instance
    """
    if extractor_type.lower() in ["guided", "ontology-guided", "8-pass", "ontology"]:
        return OntologyGuidedExtractor(api_key=api_key)
    elif extractor_type.lower() in ["robust", "7-pass", "enhanced"]:
        return RobustOntologyExtractor(api_key=api_key)
    elif extractor_type.lower() in ["standard", "4-pass", "original"]:
        return OntologyExtractor(api_key=api_key)
    else:
        raise ValueError(f"Unknown extractor type: {extractor_type}. Use 'standard', 'robust', or 'guided'")