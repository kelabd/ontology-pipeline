# src/prompts.py
"""
Centralized prompt management system for all extractors
Provides consistent, high-quality prompts with ontology guidance
"""

import json
from typing import List, Dict, Optional

class OntologyPrompts:
    """Centralized prompt system with ontology definitions and examples"""
    
    def __init__(self):
        self.ontology_definitions = {
            "construct": {
                "definition": "A specific, identifiable attribute within one or many Domains. These are key concepts to understand, track, or influence.",
                "examples": ["Breast Health", "Blood Pressure Control", "Fall Risk", "Body Composition", "Sleep Quality", "Functional Mobility", "Muscular Power", "Heart Rate Variability", "Insulin Sensitivity", "Aerobic Capacity"],
                "key_characteristics": "Can be measured, tracked over time, influenced by interventions, and have dependencies with other constructs"
            },
            "domain": {
                "definition": "A distinct, specific area of focus within one or many Dimensions, characterized by a set of related constructs.",
                "examples": ["Physical Health", "Female Health", "Cardiovascular Health", "Cognitive Health", "Stress & Adaptation", "Mental Health", "Recovery", "Performance", "Metabolic Health"],
                "key_characteristics": "Contains multiple related constructs and represents practitioner expertise areas"
            },
            "assessment": {
                "definition": "The systematic process or procedure used to evaluate the status of a Construct or progress towards a Goal, producing data that will become Metrics.",
                "examples": ["Countermovement Jump", "Mammogram", "Lipid panel", "VO2 Max Test", "DEXA Scan", "Sleep Study", "24-hour Blood Pressure Monitoring", "Hormone Panel"],
                "key_characteristics": "Has specific protocols, uses technology vendors, produces quantifiable metrics"
            },
            "technology": {
                "definition": "The specific tools, devices, software, or commercial providers used to perform an Assessment or deliver an Intervention.",
                "examples": ["VALD ForceDecks", "Neurocatch", "Oura Ring", "COSMED", "Polar H10", "LabCorp", "Quest Diagnostics", "HRV4Training", "Hologic DEXA", "SpaceLabs"],
                "key_characteristics": "Has vendor/manufacturer, specific model numbers, hardware/software classification"
            },
            "metric": {
                "definition": "A specific, measurable, and observable data point produced by an Assessment that directly contributes to understanding a Construct.",
                "examples": ["Body Fat Percentage (%)", "Systolic Blood Pressure (mmHg)", "Jump Height (cm)", "HRV (ms)", "VO2 Max (ml/kg/min)", "Estradiol (pg/mL)", "Sleep Efficiency (%)", "RER"],
                "key_characteristics": "Has specific units, reference ranges, reliability/validity characteristics"
            },
            "intervention": {
                "definition": "A specific action, programme, or strategy designed to influence, improve, or manage a particular Construct, aiming to achieve a Goal.",
                "examples": ["12-week Progressive Resistance Training", "Personalized Nutrition Plan", "Sleep Restriction Therapy", "HRV Biofeedback Training", "Aerobic Exercise Training", "Light Therapy"],
                "key_characteristics": "Has specific protocols, dosage parameters, targets specific constructs, has resource requirements"
            }
        }
    
    def get_ontology_context(self, entity_types: List[str]) -> str:
        """Generate ontology context for specified entity types"""
        context_parts = []
        
        for entity_type in entity_types:
            if entity_type in self.ontology_definitions:
                entity_info = self.ontology_definitions[entity_type]
                context_parts.append(f"""
**{entity_type.upper()} DEFINITION:** {entity_info['definition']}
**Examples:** {', '.join(entity_info['examples'][:8])}
**Key Characteristics:** {entity_info['key_characteristics']}
""")
        
        return "\n".join(context_parts)
    
    # STANDARD EXTRACTOR PROMPTS (Enhanced versions)
    
    def domains_constructs_standard(self, transcript: str) -> str:
        """Enhanced standard domain/construct extraction with ontology guidance"""
        ontology_context = self.get_ontology_context(["domain", "construct"])
        
        return f"""
You are analyzing a semi-structured interview transcript about health and performance assessment practices.

ONTOLOGY FRAMEWORK:
{ontology_context}

TRANSCRIPT:
{transcript}

Extract and return a JSON structure with:
{{
    "practitioner_domains": [
        {{
            "domain_name": "string (use terminology from examples when possible)",
            "domain_description": "string", 
            "specialization_notes": "string"
        }}
    ],
    "constructs_mentioned": [
        {{
            "construct_name": "string (use specific terminology when possible)",
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

Be precise and look for specific terminology that matches the ontology framework.
"""
    
    def assessments_standard(self, transcript: str, constructs: List[str]) -> str:
        """Enhanced standard assessment extraction with technology/metrics focus"""
        constructs_context = "\n".join([f"- {c}" for c in constructs])
        ontology_context = self.get_ontology_context(["assessment", "technology", "metric"])
        
        return f"""
Analyze this interview transcript to extract assessment information.

ONTOLOGY FRAMEWORK:
{ontology_context}

CONSTRUCTS TO ASSESS:
{constructs_context}

TRANSCRIPT:
{transcript}

For each assessment mentioned, extract:
{{
    "assessments": [
        {{
            "assessment_name": "string (exact name used)",
            "assessment_description": "string",
            "constructs_measured": ["list of constructs from above"],
            "modality": "string (Physical test/Wearable monitoring/Labs/Imaging/Survey/etc.)",
            "technology_vendor": {{
                "name": "string (exact vendor/brand name)",
                "type": "hardware/software/service",
                "specific_equipment": "string (model numbers, specific devices)"
            }},
            "protocols": {{
                "preparation_steps": ["list"],
                "coaching_cues": ["specific instructions"],
                "common_mistakes": ["errors that affect results"]
            }},
            "metrics": [
                {{
                    "metric_name": "string (exact metric name)",
                    "unit": "string (specific units: cm, kg, mmHg, %, etc.)",
                    "reference_ranges": "string (normal values mentioned)",
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
                    "asset_type": "PDF report/raw data/video/dashboard/etc.",
                    "description": "string"
                }}
            ]
        }}
    ]
}}

Hunt specifically for technology vendor names, specific equipment models, and measurable metrics with units.
"""
    
    def interventions_standard(self, transcript: str, constructs: List[str]) -> str:
        """Enhanced standard intervention extraction"""
        constructs_context = "\n".join([f"- {c}" for c in constructs])
        ontology_context = self.get_ontology_context(["intervention"])
        
        return f"""
Analyze this transcript for intervention information.

ONTOLOGY FRAMEWORK:
{ontology_context}

CONSTRUCTS TO TARGET:
{constructs_context}

TRANSCRIPT:
{transcript}

Extract:
{{
    "interventions": [
        {{
            "intervention_name": "string (exact name used)",
            "intervention_description": "string",
            "purpose": "string",
            "constructs_targeted": ["which constructs from above list"],
            "intervention_types": ["Physical/Nutrition/Sleep/Stress Management/Medical/Education/Recovery"],
            "protocols": {{
                "duration": "string (specific timeframes)",
                "frequency": "string (how often)",
                "intensity": "string (how hard/strong)",
                "volume": "string (how much)",
                "progression_criteria": ["when/how to advance"],
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

Look for specific protocols, dosage details, and resource requirements.
"""
    
    def relationships_standard(self, transcript: str, all_entities: Dict) -> str:
        """Enhanced relationship extraction"""
        return f"""
Based on this interview transcript and the entities already identified, extract relationships:

IDENTIFIED ENTITIES:
{json.dumps(all_entities, indent=2)[:1000]}...

TRANSCRIPT:
{transcript}

Extract:
{{
    "construct_relationships": [
        {{
            "source_construct": "string",
            "target_construct": "string", 
            "relationship_type": "causal/association/dependency",
            "relationship_description": "string",
            "evidence_mentioned": "string",
            "directionality": "bidirectional/unidirectional"
        }}
    ],
    "assessment_intervention_links": [
        {{
            "assessment_name": "string",
            "intervention_name": "string",
            "connection_type": "informs/measures_progress/triggers/evaluates",
            "description": "string"
        }}
    ],
    "goal_connections": [
        {{
            "goal_description": "string",
            "target_constructs": ["list"],
            "supporting_assessments": ["list"],
            "recommended_interventions": ["list"]
        }}
    ]
}}
"""
    
    # ONTOLOGY-GUIDED EXTRACTOR PROMPTS
    
    def knowledge_mapping_guided(self, transcript: str) -> str:
        """Comprehensive knowledge domain mapping"""
        return f"""
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
    
    def constructs_guided(self, transcript: str, expertise_context: str = "") -> str:
        """Ontology-guided construct extraction"""
        ontology_context = self.get_ontology_context(["construct"])
        
        return f"""
Extract ALL constructs using this specific ontology definition.

ONTOLOGY FRAMEWORK:
{ontology_context}

EXPERTISE CONTEXT: {expertise_context}

TRANSCRIPT:
{transcript}

Look specifically for attributes that practitioners measure, track, or influence. Use exact terminology when possible.

Extract:
{{
    "constructs_mentioned": [
        {{
            "construct_name": "string (use specific terminology when possible)",
            "construct_description": "string",
            "domain_association": "string",
            "why_important": "string (why practitioner focuses on this)",
            "how_assessed": "string (how they evaluate this construct)",
            "measurement_approach": "string"
        }}
    ],
    "health_performance_factors": [
        {{
            "factor_name": "string",
            "factor_type": "string (physiological/psychological/behavioral/environmental)",
            "description": "string",
            "measurement_approach": "string"
        }}
    ]
}}

Be specific - look for exact terminology like "sleep quality," "muscular power," "insulin sensitivity," etc.
"""
    
    def assessments_guided(self, transcript: str, constructs: List[str]) -> str:
        """Ontology-guided assessment extraction"""
        constructs_context = ", ".join(constructs[:10])
        ontology_context = self.get_ontology_context(["assessment"])
        
        return f"""
Extract ALL assessments using this specific definition.

ONTOLOGY FRAMEWORK:
{ontology_context}

CONSTRUCTS IDENTIFIED: {constructs_context}

TRANSCRIPT:
{transcript}

Look for ANY method used to evaluate, test, measure, or gather information about the constructs above.

Extract all assessments:
{{
    "assessments": [
        {{
            "assessment_name": "string (exact name used)",
            "assessment_description": "string",
            "constructs_measured": ["list - which constructs does this assess"],
            "modality": "string (Physical test/Wearable monitoring/Consultation/Labs/Imaging/Survey/etc)",
            "administration_details": {{
                "where_performed": "string (lab/clinic/field/home)",
                "duration": "string",
                "preparation_required": "string",
                "frequency": "string"
            }},
            "protocol_details": {{
                "key_steps": ["list of main protocol steps"],
                "coaching_cues": ["specific instructions given"],
                "common_mistakes": ["errors that affect results"],
                "quality_controls": ["how to ensure good data"]
            }}
        }}
    ]
}}

Include formal tests, informal observations, questionnaires, monitoring approaches - anything used to gather assessment data.
"""
    
    def technologies_metrics_guided(self, transcript: str, assessments: List[str]) -> str:
        """Dedicated technology and metrics extraction"""
        tech_context = self.get_ontology_context(["technology", "metric"])
        assessments_context = ", ".join(assessments[:10])
        
        return f"""
Extract ALL technologies and metrics mentioned in this interview.

ONTOLOGY FRAMEWORK:
{tech_context}

ASSESSMENTS IDENTIFIED: {assessments_context}

TRANSCRIPT:
{transcript}

Hunt specifically for:
1. Equipment brands, models, software names
2. Specific measurable outputs with units
3. Any vendor or manufacturer names
4. Specific measurement values or ranges

Extract technologies and metrics:
{{
    "technologies": [
        {{
            "technology_name": "string (exact name/brand mentioned)",
            "vendor_manufacturer": "string (company name)",
            "technology_type": "string (hardware/software/device/service)",
            "specific_model": "string (if mentioned)",
            "used_for_assessments": ["which assessments use this"],
            "what_it_measures": ["capabilities it assesses"],
            "data_output_format": "string (PDF report/raw data/dashboard/etc)",
            "mentioned_advantages": ["benefits mentioned"],
            "mentioned_limitations": ["constraints mentioned"]
        }}
    ],
    "metrics": [
        {{
            "metric_name": "string (exact name used)",
            "measurement_unit": "string (cm, kg, mmHg, %, etc)",
            "assessment_source": "string (which assessment produces this)",
            "normal_ranges": "string (any reference values mentioned)",
            "interpretation_notes": "string (how values are interpreted)",
            "factors_affecting_values": ["what influences this measurement"],
            "reliability_notes": "string (confidence/validity mentioned)"
        }}
    ],
    "measurement_contexts": [
        {{
            "context_description": "string",
            "specific_values_mentioned": ["any specific numbers, ranges, or thresholds"],
            "reference_populations": ["athlete/health seeker/age groups/etc"],
            "timing_considerations": ["when measurements are taken"]
        }}
    ]
}}

Look for specific brand names, model numbers, measurement units, reference ranges, and any quantitative values mentioned.
"""
    
    def interventions_guided(self, transcript: str, constructs: List[str]) -> str:
        """Ontology-guided intervention extraction"""
        intervention_context = self.get_ontology_context(["intervention"])
        constructs_context = ", ".join(constructs[:10])
        
        return f"""
Extract ALL interventions using this specific definition.

ONTOLOGY FRAMEWORK:
{intervention_context}

CONSTRUCTS TO TARGET: {constructs_context}

TRANSCRIPT:
{transcript}

Look for ANY strategy, program, treatment, or approach used to improve the constructs above.

Extract all interventions:
{{
    "interventions": [
        {{
            "intervention_name": "string (exact name used)",
            "intervention_description": "string",
            "purpose": "string (what it aims to achieve)",
            "constructs_targeted": ["which constructs does this improve"],
            "intervention_types": ["Physical/Nutrition/Sleep/Stress Management/Medical/Education/Recovery"],
            "dosage_details": {{
                "frequency": "string (how often)",
                "duration": "string (how long)",
                "intensity": "string (how hard/strong)",
                "volume": "string (how much)",
                "progression": "string (how it advances)"
            }},
            "implementation_specifics": {{
                "delivery_method": "string (how it's delivered)",
                "monitoring_approach": "string (how progress is tracked)",
                "adjustment_criteria": "string (when/how it's modified)"
            }},
            "resource_requirements": {{
                "equipment_needed": ["list"],
                "time_commitment": "string",
                "expertise_required": "string",
                "cost_level": "string (High/Moderate/Low if mentioned)"
            }}
        }}
    ]
}}

Include exercise programs, nutrition plans, lifestyle modifications, medical treatments, education protocols - anything designed to improve health/performance outcomes.
"""
    
    def validation_guided(self, transcript: str, all_extractions: Dict) -> str:
        """Validation and gap identification"""
        return f"""
Review this transcript and the extracted information to identify any significant gaps.

TRANSCRIPT EXCERPT (first 1500 chars):
{transcript[:1500]}...

Perform ontology validation:
{{
    "ontology_coverage_check": {{
        "constructs_identified": {len(all_extractions.get('constructs', {}).get('constructs_mentioned', []))},
        "assessments_identified": {len(all_extractions.get('assessments', {}).get('assessments', []))},
        "interventions_identified": {len(all_extractions.get('interventions', {}).get('interventions', []))},
        "technologies_identified": {len(all_extractions.get('technologies', {}).get('technologies', []))},
        "metrics_identified": {len(all_extractions.get('technologies', {}).get('metrics', []))}
    }},
    "potential_missed_entities": [
        {{
            "entity_type": "string (construct/assessment/intervention/technology/metric)",
            "potential_entity": "string",
            "evidence_in_transcript": "string",
            "confidence": "string (high/medium/low)"
        }}
    ],
    "quality_assessment": {{
        "extraction_completeness": "string (high/medium/low)",
        "terminology_consistency": "string (high/medium/low)",
        "relationship_coverage": "string (high/medium/low)",
        "overall_confidence": "string (high/medium/low)"
    }},
    "recommendations": [
        {{
            "recommendation_type": "string",
            "description": "string",
            "priority": "string (high/medium/low)"
        }}
    ]
}}
"""

# Legacy class for backward compatibility
class ExtractionPrompts(OntologyPrompts):
    """Legacy prompt class - redirects to new system"""
    
    def __init__(self):
        super().__init__()
        print("⚠️  Using legacy ExtractionPrompts. Consider upgrading to OntologyPrompts.")
    
    def domains_constructs_prompt(self, transcript: str) -> str:
        return self.domains_constructs_standard(transcript)
    
    def assessments_prompt(self, transcript: str, constructs: List[str]) -> str:
        return self.assessments_standard(transcript, constructs)
    
    def interventions_prompt(self, transcript: str, constructs: List[str]) -> str:
        return self.interventions_standard(transcript, constructs)
    
    def relationships_prompt(self, transcript: str, all_entities: Dict) -> str:
        return self.relationships_standard(transcript, all_entities)