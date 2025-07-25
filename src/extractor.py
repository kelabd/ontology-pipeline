# src/extractor.py
"""
Unified extraction system with multiple extractor options
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

from src.prompts import ExtractionPrompts
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
        self.prompts = ExtractionPrompts()
        
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
        """Clean Claude's response to extract pure JSON"""
        text = text.strip()
        
        if text.startswith('```json'):
            text = text[7:]
        elif text.startswith('```'):
            text = text[3:]
        
        if text.endswith('```'):
            text = text[:-3]
        
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
    """Original 4-pass extraction system"""
    
    def __init__(self, api_key=None):
        super().__init__(api_key)
        self.extraction_type = "Standard (4-pass)"
        print("✅ Standard Extractor initialized successfully")
        print("🔄 Using 4-pass extraction strategy")
    
    def extract_domains_constructs(self, transcript: str) -> Dict:
        """Extract domains and constructs mentioned in the interview"""
        prompt = self.prompts.domains_constructs_prompt(transcript)
        response_text = self.make_api_call(prompt)
        return self.safe_json_parse(response_text)
    
    def extract_assessments(self, transcript: str, constructs: List[str]) -> Dict:
        """Extract detailed assessment information"""
        prompt = self.prompts.assessments_prompt(transcript, constructs)
        response_text = self.make_api_call(prompt)
        return self.safe_json_parse(response_text)
    
    def extract_interventions(self, transcript: str, constructs: List[str]) -> Dict:
        """Extract intervention information and protocols"""
        prompt = self.prompts.interventions_prompt(transcript, constructs)
        response_text = self.make_api_call(prompt)
        return self.safe_json_parse(response_text)
    
    def extract_relationships(self, transcript: str, all_entities: Dict) -> Dict:
        """Extract construct relationships and dependencies"""
        prompt = self.prompts.relationships_prompt(transcript, all_entities)
        response_text = self.make_api_call(prompt)
        return self.safe_json_parse(response_text)
    
    def process_single_transcript(self, file_path: Path) -> Dict:
        """Process a single transcript file using standard approach"""
        print(f"📄 Processing: {file_path.name}")
        
        with open(file_path, 'r', encoding='utf-8') as f:
            transcript = f.read()
        
        # 4-pass extraction
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
        """Process all transcripts in a folder using standard approach"""
        folder = Path(folder_path)
        if not folder.exists():
            raise ValueError(f"Folder does not exist: {folder_path}")
        
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
                "failed": 0,
                "extraction_type": self.extraction_type
            }
        }
        
        for i, file_path in enumerate(transcript_files, 1):
            try:
                print(f"\n[{i}/{len(transcript_files)}]", end=" ")
                file_result = self.process_single_transcript(file_path)
                results["processed_files"].append(file_result)
                results["summary"]["successful"] += 1
                
                # Small delay for API rate limiting
                time.sleep(0.5)
                
            except Exception as e:
                print(f"❌ Error processing {file_path.name}: {e}")
                results["processed_files"].append({
                    "file_name": file_path.name,
                    "error": str(e)
                })
                results["summary"]["failed"] += 1
        
        return results

class RobustOntologyExtractor(BaseOntologyExtractor):
    """Enhanced 7-pass extraction system for maximum information capture"""
    
    def __init__(self, api_key=None):
        super().__init__(api_key)
        self.extraction_type = "Robust (7-pass)"
        print("✅ Robust Extractor initialized successfully")
        print("🔄 Using 7-pass robust extraction strategy")
    
    def extract_knowledge_domains(self, transcript: str) -> Dict:
        """Pass 1: Open-ended knowledge domain mapping"""
        prompt = f"""
        Analyze this interview transcript to create a comprehensive knowledge map. Be expansive and inclusive - capture ALL areas of expertise, knowledge domains, and specializations mentioned.

        TRANSCRIPT:
        {transcript}

        Extract and return JSON:
        {{
            "primary_expertise": [
                {{
                    "area": "string",
                    "description": "string",
                    "scope": "string",
                    "depth_indicators": ["specific examples showing depth"]
                }}
            ],
            "knowledge_domains": [
                {{
                    "domain": "string", 
                    "description": "string",
                    "sub_areas": ["list of sub-specializations"]
                }}
            ],
            "target_populations": [
                {{
                    "population": "string",
                    "characteristics": "string",
                    "specific_needs": "string"
                }}
            ]
        }}
        """
        
        response = self.make_api_call(prompt, max_tokens=4000)
        return self.safe_json_parse(response)
    
    def extract_comprehensive_entities(self, transcript: str, knowledge_map: Dict) -> Dict:
        """Pass 2: Comprehensive entity extraction without predefined constraints"""
        
        expertise_context = ""
        if knowledge_map and "primary_expertise" in knowledge_map:
            expertise_areas = [area.get("area", "") for area in knowledge_map["primary_expertise"]]
            expertise_context = f"Primary expertise: {', '.join(expertise_areas)}"
        
        prompt = f"""
        Extract ALL measurable, trackable, or influenceable concepts from this interview. Cast a wide net - include anything the practitioner considers important to assess, track, monitor, or influence.

        CONTEXT: {expertise_context}

        TRANSCRIPT:
        {transcript}

        Extract comprehensive entities:
        {{
            "measurable_concepts": [
                {{
                    "concept_name": "string",
                    "description": "string",
                    "category": "string",
                    "why_important": "string",
                    "measurement_approach": "string"
                }}
            ],
            "capabilities_and_attributes": [
                {{
                    "capability": "string",
                    "description": "string",
                    "components": ["sub-components"],
                    "assessment_indicators": ["how to recognize this capability"]
                }}
            ],
            "health_performance_states": [
                {{
                    "state": "string",
                    "description": "string", 
                    "indicators": ["how to recognize this state"],
                    "influencing_factors": ["what affects this state"]
                }}
            ]
        }}
        """
        
        response = self.make_api_call(prompt, max_tokens=4000)
        return self.safe_json_parse(response)
    
    def extract_detailed_assessments(self, transcript: str, entities: Dict) -> Dict:
        """Pass 3: Detailed assessment extraction"""
        prompt = f"""
        Extract ALL assessment and evaluation methods mentioned in this interview.

        TRANSCRIPT:
        {transcript}

        Extract comprehensive assessments:
        {{
            "formal_assessments": [
                {{
                    "assessment_name": "string",
                    "description": "string",
                    "what_it_measures": ["list of concepts/capabilities assessed"],
                    "assessment_type": "string",
                    "administration_context": "string",
                    "frequency_timing": "string"
                }}
            ],
            "protocols_and_procedures": [
                {{
                    "assessment_name": "string", 
                    "detailed_protocol": "string",
                    "preparation_requirements": ["list"],
                    "step_by_step_process": ["ordered list"],
                    "quality_control_measures": ["how to ensure good data"]
                }}
            ],
            "technologies_and_equipment": [
                {{
                    "technology_name": "string",
                    "vendor_manufacturer": "string",
                    "equipment_type": "string",
                    "what_it_measures": ["capabilities"],
                    "advantages": ["benefits"],
                    "limitations": ["constraints"]
                }}
            ]
        }}
        """
        
        response = self.make_api_call(prompt, max_tokens=4000)
        return self.safe_json_parse(response)
    
    def extract_detailed_interventions(self, transcript: str, entities: Dict) -> Dict:
        """Pass 4: Detailed intervention extraction"""
        prompt = f"""
        Extract ALL intervention strategies, treatments, programs, and approaches mentioned.

        TRANSCRIPT:
        {transcript}

        Extract comprehensive interventions:
        {{
            "intervention_strategies": [
                {{
                    "intervention_name": "string",
                    "description": "string",
                    "intervention_category": "string",
                    "target_outcomes": ["what this intervention aims to improve"],
                    "mechanism_of_action": "string",
                    "typical_candidates": "string"
                }}
            ],
            "detailed_protocols": [
                {{
                    "intervention_name": "string",
                    "dosage_parameters": {{
                        "frequency": "string",
                        "duration": "string",
                        "intensity": "string",
                        "progression_rules": "string"
                    }},
                    "implementation_details": "string",
                    "monitoring_requirements": ["what to track"]
                }}
            ],
            "resource_requirements": [
                {{
                    "intervention_name": "string",
                    "equipment_needed": ["list"],
                    "time_investment": "string",
                    "expertise_level_required": "string"
                }}
            ]
        }}
        """
        
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
        contextual_info = self.extract_contextual_factors(transcript, entities)
        
        print("  🔗 Pass 6: Comprehensive relationships...")
        relationships = self.extract_comprehensive_relationships(transcript, {
            'knowledge_map': knowledge_map,
            'entities': entities,
            'assessments': assessments,
            'interventions': interventions
        })
        
        print("  ✅ Pass 7: Validation and enhancement...")
        validation = self.validate_and_enhance(transcript, {
            'knowledge_map': knowledge_map,
            'entities': entities,
            'assessments': assessments,
            'interventions': interventions,
            'relationships': relationships
        })
        
        # Calculate constructs for compatibility
        total_constructs = 0
        if entities and isinstance(entities, dict):
            for category in entities.values():
                if isinstance(category, list):
                    total_constructs += len(category)
        
        # Create legacy-compatible format
        legacy_domains_constructs = self.convert_to_legacy_domains(knowledge_map, entities)
        legacy_assessments = self.convert_to_legacy_assessments(assessments)
        legacy_interventions = self.convert_to_legacy_interventions(interventions)
        
        result = {
            "file_name": file_path.name,
            "transcript_length": len(transcript),
            "constructs_identified": total_constructs,
            
            # Legacy format for compatibility
            "domains_constructs": legacy_domains_constructs,
            "assessments": legacy_assessments,
            "interventions": legacy_interventions,
            "relationships": relationships,
            
            # Enhanced robust data
            "robust_data": {
                "knowledge_map": knowledge_map,
                "entities": entities,
                "detailed_assessments": assessments,
                "detailed_interventions": interventions,
                "contextual_info": contextual_info,
                "validation": validation
            }
        }
        
        print(f"  ✅ Found {total_constructs} total entities")
        return result
    
    def convert_to_legacy_domains(self, knowledge_map: Dict, entities: Dict) -> Dict:
        """Convert to legacy format for compatibility"""
        legacy = {
            "practitioner_domains": [],
            "constructs_mentioned": [],
            "sport_specificity": []
        }
        
        # Convert expertise to domains
        if knowledge_map and "primary_expertise" in knowledge_map:
            for expertise in knowledge_map["primary_expertise"]:
                legacy["practitioner_domains"].append({
                    "domain_name": expertise.get("area", ""),
                    "domain_description": expertise.get("description", ""),
                    "specialization_notes": expertise.get("scope", "")
                })
        
        # Convert entities to constructs
        if entities:
            for category, items in entities.items():
                if isinstance(items, list):
                    for item in items:
                        name_key = next((k for k in ['concept_name', 'capability', 'state'] if k in item), None)
                        if name_key and item[name_key]:
                            legacy["constructs_mentioned"].append({
                                "construct_name": item[name_key],
                                "construct_description": item.get("description", ""),
                                "domain_association": category,
                                "assessment_context": item.get("measurement_approach", "")
                            })
        
        return legacy
    
    def convert_to_legacy_assessments(self, assessments: Dict) -> Dict:
        """Convert assessments to legacy format"""
        if not assessments or "formal_assessments" not in assessments:
            return {"assessments": []}
        
        legacy_assessments = []
        for assessment in assessments["formal_assessments"]:
            legacy_assessments.append({
                "assessment_name": assessment.get("assessment_name", ""),
                "assessment_description": assessment.get("description", ""),
                "constructs_measured": assessment.get("what_it_measures", []),
                "modality": assessment.get("assessment_type", ""),
                "technology_vendor": {},
                "protocols": {},
                "metrics": [],
                "state_influences": [],
                "assets_generated": []
            })
        
        return {"assessments": legacy_assessments}
    
    def convert_to_legacy_interventions(self, interventions: Dict) -> Dict:
        """Convert interventions to legacy format"""
        if not interventions or "intervention_strategies" not in interventions:
            return {"interventions": []}
        
        legacy_interventions = []
        for intervention in interventions["intervention_strategies"]:
            legacy_interventions.append({
                "intervention_name": intervention.get("intervention_name", ""),
                "intervention_description": intervention.get("description", ""),
                "purpose": ", ".join(intervention.get("target_outcomes", [])),
                "constructs_targeted": intervention.get("target_outcomes", []),
                "intervention_types": [intervention.get("intervention_category", "")],
                "protocols": {},
                "resource_requirements": {}
            })
        
        return {"interventions": legacy_interventions}
    
    def process_transcript_folder(self, folder_path: str) -> Dict:
        """Process all transcripts using robust extraction"""
        folder = Path(folder_path)
        if not folder.exists():
            raise ValueError(f"Folder does not exist: {folder_path}")
        
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
                "failed": 0,
                "extraction_type": self.extraction_type,
                "total_api_calls": 0
            }
        }
        
        for i, file_path in enumerate(transcript_files, 1):
            try:
                print(f"\n[{i}/{len(transcript_files)}]", end=" ")
                file_result = self.process_single_transcript(file_path)
                results["processed_files"].append(file_result)
                results["summary"]["successful"] += 1
                results["summary"]["total_api_calls"] += 7  # 7 passes
                
                # Small delay for API rate limiting
                time.sleep(1)
                
            except Exception as e:
                print(f"❌ Error processing {file_path.name}: {e}")
                results["processed_files"].append({
                    "file_name": file_path.name,
                    "error": str(e)
                })
                results["summary"]["failed"] += 1
        
        return results

# Factory function for easy extractor selection
def create_extractor(extractor_type: str = "standard", api_key: Optional[str] = None):
    """
    Factory function to create the appropriate extractor
    
    Args:
        extractor_type: "standard" for 4-pass or "robust" for 7-pass
        api_key: Optional API key
    
    Returns:
        Configured extractor instance
    """
    if extractor_type.lower() in ["robust", "7-pass", "enhanced"]:
        return RobustOntologyExtractor(api_key=api_key)
    elif extractor_type.lower() in ["standard", "4-pass", "original"]:
        return OntologyExtractor(api_key=api_key)
    else:
        raise ValueError(f"Unknown extractor type: {extractor_type}. Use 'standard' or 'robust'")