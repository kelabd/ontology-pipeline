# src/prompts.py
import json

class ExtractionPrompts:
    """All extraction prompts for the ontology pipeline"""
    
    @staticmethod
    def domains_constructs_prompt(transcript: str) -> str:
        return f"""
You are analyzing a semi-structured interview transcript about health and performance assessment practices. 

ONTOLOGY CONTEXT:
- Dimensions: Fundamental aspects (Health, Performance)
- Domains: Specific focus areas (Physical Health, Female Health, Cardiovascular Health, etc.)
- Constructs: Specific attributes to understand/track/influence (Sleep Quality, Blood Pressure Control, etc.)

TRANSCRIPT:
{transcript}

Extract and return a JSON structure with:
{{
    "practitioner_domains": [
        {{
            "domain_name": "string",
            "domain_description": "string", 
            "specialization_notes": "string"
        }}
    ],
    "constructs_mentioned": [
        {{
            "construct_name": "string",
            "construct_description": "string",
            "domain_association": "string",
            "assessment_context": "string"
        }}
    ],
    "sport_specificity": [
        {{
            "sport": "string",
            "assessment_modifications": "string",
            "intervention_modifications": "string"
        }}
    ]
}}

Be precise and only extract information explicitly mentioned in the transcript.
"""
    
    @staticmethod
    def assessments_prompt(transcript: str, constructs: list) -> str:
        constructs_context = "\n".join([f"- {c}" for c in constructs])
        
        return f"""
Analyze this interview transcript to extract assessment information. Focus on the constructs identified: 
{constructs_context}

TRANSCRIPT:
{transcript}

For each assessment mentioned, extract:
{{
    "assessments": [
        {{
            "assessment_name": "string",
            "assessment_description": "string",
            "constructs_measured": ["list of constructs"],
            "modality": "string (Physical test/Wearable monitoring/etc.)",
            "technology_vendor": {{
                "name": "string",
                "type": "hardware/software",
                "specific_equipment": "string"
            }},
            "protocols": {{
                "preparation_steps": ["list"],
                "coaching_cues": ["list"],
                "common_mistakes": ["list"]
            }},
            "metrics": [
                {{
                    "metric_name": "string",
                    "unit": "string",
                    "reference_ranges": "string",
                    "validity_confidence": "string",
                    "reliability_confidence": "string"
                }}
            ],
            "state_influences": [
                {{
                    "state_name": "string",
                    "impact_on_assessment": "string",
                    "impact_on_interpretation": "string"
                }}
            ],
            "assets_generated": [
                {{
                    "asset_name": "string",
                    "asset_type": "PDF report/raw data/video/etc.",
                    "description": "string"
                }}
            ]
        }}
    ]
}}

Return only valid JSON.
"""
    
    @staticmethod
    def interventions_prompt(transcript: str, constructs: list) -> str:
        constructs_context = "\n".join([f"- {c}" for c in constructs])
        
        return f"""
Analyze this transcript for intervention information targeting these constructs:
{constructs_context}

TRANSCRIPT:
{transcript}

Extract:
{{
    "interventions": [
        {{
            "intervention_name": "string",
            "intervention_description": "string",
            "purpose": "string",
            "constructs_targeted": ["list"],
            "intervention_types": ["Physical/Nutrition/Sleep/etc."],
            "protocols": {{
                "duration": "string",
                "frequency": "string",
                "intensity": "string",
                "volume": "string",
                "progression_criteria": ["list"],
                "reassessment_intervals": "string"
            }},
            "constraints_accommodations": [
                {{
                    "constraint_type": "string",
                    "accommodation_strategy": "string"
                }}
            ],
            "resource_requirements": {{
                "time": "string",
                "equipment": "string",
                "staff_expertise": "string",
                "cost_level": "High/Moderate/Low"
            }}
        }}
    ]
}}

Return only valid JSON.
"""