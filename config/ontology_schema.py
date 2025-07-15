# config/ontology_schema.py
ONTOLOGY_SCHEMA = {
    "dimensions": {
        "Health": "A fundamental aspect focusing on physical and mental wellbeing",
        "Performance": "A fundamental aspect focusing on athletic and cognitive performance"
    },
    "domains": [
        "Physical Health", "Female Health", "Cardiovascular Health", 
        "Cognitive Health", "Stress & Adaptation", "Mental Health", "Recovery"
    ],
    "constructs": [
        "Breast Health", "Blood Pressure Control", "Fall Risk", 
        "Body Composition", "Sleep Quality", "Functional Mobility"
    ],
    "assessment_types": [
        "Imaging", "Bloodwork", "Survey", "Field Test", 
        "Performance Test", "Clinical Consultation"
    ],
    "intervention_types": [
        "Physical", "Nutrition", "Sleep", "Stress Management", 
        "Medical", "Education", "Recovery"
    ],
    "modalities": [
        "Physical test", "Wearable monitoring", "Consultation", 
        "Cognitive assessment", "Survey", "Imaging", "Labs/bloodwork", 
        "Intake", "Prevention"
    ]
}