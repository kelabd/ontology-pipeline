import streamlit as st
import json
import pandas as pd
import plotly.express as px
import plotly.graph_objects as go
from collections import defaultdict, Counter
import os

# Configure page
st.set_page_config(
    page_title="Ontology Extraction Explorer",
    page_icon="🧠",
    layout="wide",
    initial_sidebar_state="expanded"
)

# Custom CSS for better styling
st.markdown("""
<style>
    .metric-card {
        background-color: #f0f2f6;
        padding: 1rem;
        border-radius: 0.5rem;
        margin: 0.5rem 0;
    }
    .construct-badge {
        background-color: #e1f5fe;
        color: #01579b;
        padding: 0.2rem 0.5rem;
        border-radius: 1rem;
        margin: 0.2rem;
        display: inline-block;
        font-size: 0.8rem;
    }
    .assessment-badge {
        background-color: #f3e5f5;
        color: #4a148c;
        padding: 0.2rem 0.5rem;
        border-radius: 1rem;
        margin: 0.2rem;
        display: inline-block;
        font-size: 0.8rem;
    }
    .intervention-badge {
        background-color: #e8f5e8;
        color: #1b5e20;
        padding: 0.2rem 0.5rem;
        border-radius: 1rem;
        margin: 0.2rem;
        display: inline-block;
        font-size: 0.8rem;
    }
</style>
""", unsafe_allow_html=True)

@st.cache_data
def load_extraction_data():
    """Load the extraction results with caching"""
    try:
        with open('data/outputs/extraction_results.json', 'r') as f:
            data = json.load(f)
        return data
    except FileNotFoundError:
        st.error("⚠️ extraction_results.json not found. Please run the extraction pipeline first.")
        return None
    except json.JSONDecodeError:
        st.error("⚠️ Invalid JSON format in extraction_results.json")
        return None

def extract_all_entities(data):
    """Extract and organize all entities from the data"""
    entities = {
        'domains': {},
        'constructs': {},
        'assessments': {},
        'interventions': {},
        'technologies': {},
        'metrics': {}
    }

    for file_data in data.get('processed_files', []):
        if 'error' in file_data:
            continue

        file_name = file_data.get('file_name', 'Unknown')

        # Domains & Constructs
        domains_constructs = file_data.get('domains_constructs', {})
        for domain in domains_constructs.get('practitioner_domains', []):
            domain_name = domain.get('domain_name', '')
            if domain_name:
                if domain_name not in entities['domains']:
                    entities['domains'][domain_name] = {
                        'description': domain.get('domain_description', ''),
                        'files': [],
                        'specialization_notes': []
                    }
                entities['domains'][domain_name]['files'].append(file_name)
                entities['domains'][domain_name]['specialization_notes'].append(
                    domain.get('specialization_notes', '')
                )

        for construct in domains_constructs.get('constructs_mentioned', []):
            construct_name = construct.get('construct_name', '')
            if construct_name:
                if construct_name not in entities['constructs']:
                    entities['constructs'][construct_name] = {
                        'description': construct.get('construct_description', ''),
                        'domain_association': construct.get('domain_association', ''),
                        'files': [],
                        'assessment_contexts': []
                    }
                entities['constructs'][construct_name]['files'].append(file_name)
                entities['constructs'][construct_name]['assessment_contexts'].append(
                    construct.get('assessment_context', '')
                )

        # Assessments
        assessments_data = file_data.get('assessments', {})
        for assessment in assessments_data.get('assessments', []):
            assessment_name = assessment.get('assessment_name', '')
            if assessment_name:
                if assessment_name not in entities['assessments']:
                    entities['assessments'][assessment_name] = {
                        'description': assessment.get('assessment_description', ''),
                        'modality': assessment.get('modality', ''),
                        'constructs_measured': assessment.get('constructs_measured', []),
                        'files': [],
                        'technologies': [],
                        'metrics': []
                    }
                entities['assessments'][assessment_name]['files'].append(file_name)

        # Interventions
        interventions_data = file_data.get('interventions', {})
        for intervention in interventions_data.get('interventions', []):
            intervention_name = intervention.get('intervention_name', '')
            if intervention_name:
                if intervention_name not in entities['interventions']:
                    entities['interventions'][intervention_name] = {
                        'description': intervention.get('intervention_description', ''),
                        'purpose': intervention.get('purpose', ''),
                        'constructs_targeted': intervention.get('constructs_targeted', []),
                        'intervention_types': intervention.get('intervention_types', []),
                        'files': []
                    }
                entities['interventions'][intervention_name]['files'].append(file_name)

        # 🧠 ADD Technologies & Metrics from `ontology_guided_data`
        tech_metrics = file_data.get('ontology_guided_data', {}).get('technologies_metrics', {})
        for tech in tech_metrics.get('technologies', []):
            tech_name = tech.get('technology_name', '')
            if tech_name:
                if tech_name not in entities['technologies']:
                    entities['technologies'][tech_name] = {
                        'type': tech.get('technology_type', ''),
                        'equipment': tech.get('specific_model', ''),
                        'used_in_assessments': tech.get('used_for_assessments', []),
                        'files': []
                    }
                entities['technologies'][tech_name]['files'].append(file_name)

        for metric in tech_metrics.get('metrics', []):
            metric_name = metric.get('metric_name', '')
            if metric_name:
                if metric_name not in entities['metrics']:
                    entities['metrics'][metric_name] = {
                        'unit': metric.get('measurement_unit', ''),
                        'reference_ranges': metric.get('normal_ranges', ''),
                        'validity_confidence': metric.get('interpretation_notes', ''),
                        'used_in_assessments': [metric.get('assessment_source', '')],
                        'files': []
                    }
                entities['metrics'][metric_name]['files'].append(file_name)

    return entities

    """Extract and organize all entities from the data"""
    entities = {
        'domains': {},
        'constructs': {},
        'assessments': {},
        'interventions': {},
        'technologies': {},
        'metrics': {}
    }
    
    for file_data in data.get('processed_files', []):
        if 'error' in file_data:
            continue
            
        file_name = file_data.get('file_name', 'Unknown')
        
        # Extract domains
        domains_constructs = file_data.get('domains_constructs', {})
        for domain in domains_constructs.get('practitioner_domains', []):
            domain_name = domain.get('domain_name', '')
            if domain_name:
                if domain_name not in entities['domains']:
                    entities['domains'][domain_name] = {
                        'description': domain.get('domain_description', ''),
                        'files': [],
                        'specialization_notes': []
                    }
                entities['domains'][domain_name]['files'].append(file_name)
                entities['domains'][domain_name]['specialization_notes'].append(
                    domain.get('specialization_notes', '')
                )
        
        # Extract constructs
        for construct in domains_constructs.get('constructs_mentioned', []):
            construct_name = construct.get('construct_name', '')
            if construct_name:
                if construct_name not in entities['constructs']:
                    entities['constructs'][construct_name] = {
                        'description': construct.get('construct_description', ''),
                        'domain_association': construct.get('domain_association', ''),
                        'files': [],
                        'assessment_contexts': []
                    }
                entities['constructs'][construct_name]['files'].append(file_name)
                entities['constructs'][construct_name]['assessment_contexts'].append(
                    construct.get('assessment_context', '')
                )
        
        # Extract assessments
        assessments_data = file_data.get('assessments', {})
        for assessment in assessments_data.get('assessments', []):
            assessment_name = assessment.get('assessment_name', '')
            if assessment_name:
                if assessment_name not in entities['assessments']:
                    entities['assessments'][assessment_name] = {
                        'description': assessment.get('assessment_description', ''),
                        'modality': assessment.get('modality', ''),
                        'constructs_measured': assessment.get('constructs_measured', []),
                        'files': [],
                        'technologies': [],
                        'metrics': []
                    }
                entities['assessments'][assessment_name]['files'].append(file_name)
                
                # Extract technology
                tech = assessment.get('technology_vendor', {})
                if tech.get('name'):
                    entities['assessments'][assessment_name]['technologies'].append(tech)
                    
                    # Add to technologies collection
                    tech_name = tech.get('name', '')
                    if tech_name not in entities['technologies']:
                        entities['technologies'][tech_name] = {
                            'type': tech.get('type', ''),
                            'equipment': tech.get('specific_equipment', ''),
                            'used_in_assessments': [],
                            'files': []
                        }
                    entities['technologies'][tech_name]['used_in_assessments'].append(assessment_name)
                    entities['technologies'][tech_name]['files'].append(file_name)
                
                # Extract metrics
                for metric in assessment.get('metrics', []):
                    metric_name = metric.get('metric_name', '')
                    if metric_name:
                        entities['assessments'][assessment_name]['metrics'].append(metric)
                        
                        if metric_name not in entities['metrics']:
                            entities['metrics'][metric_name] = {
                                'unit': metric.get('unit', ''),
                                'reference_ranges': metric.get('reference_ranges', ''),
                                'validity_confidence': metric.get('validity_confidence', ''),
                                'used_in_assessments': [],
                                'files': []
                            }
                        entities['metrics'][metric_name]['used_in_assessments'].append(assessment_name)
                        entities['metrics'][metric_name]['files'].append(file_name)
        
        # Extract interventions
        interventions_data = file_data.get('interventions', {})
        for intervention in interventions_data.get('interventions', []):
            intervention_name = intervention.get('intervention_name', '')
            if intervention_name:
                if intervention_name not in entities['interventions']:
                    entities['interventions'][intervention_name] = {
                        'description': intervention.get('intervention_description', ''),
                        'purpose': intervention.get('purpose', ''),
                        'constructs_targeted': intervention.get('constructs_targeted', []),
                        'intervention_types': intervention.get('intervention_types', []),
                        'files': []
                    }
                entities['interventions'][intervention_name]['files'].append(file_name)
    
    return entities

def main():
    st.title("🧠 Ontology Extraction Explorer")
    st.markdown("Explore the knowledge extracted from IST specialist interviews")
    
    # Load data
    data = load_extraction_data()
    if data is None:
        st.stop()
    
    # Extract entities
    entities = extract_all_entities(data)
    
    # Sidebar navigation
    st.sidebar.title("🔍 Navigation")
    page = st.sidebar.selectbox(
        "Choose a view:",
        ["📊 Overview", "📄 By Transcript", "🎯 Domains", "🔬 Constructs", 
         "🧪 Assessments", "💊 Interventions", "⚙️ Technologies", "📏 Metrics"]
    )
    
    if page == "📊 Overview":
        show_overview(data, entities)
    elif page == "📄 By Transcript":
        show_by_transcript(data)
    elif page == "🎯 Domains":
        show_domains(entities)
    elif page == "🔬 Constructs":
        show_constructs(entities)
    elif page == "🧪 Assessments":
        show_assessments(entities)
    elif page == "💊 Interventions":
        show_interventions(entities)
    elif page == "⚙️ Technologies":
        show_technologies(entities)
    elif page == "📏 Metrics":
        show_metrics(entities)

def show_overview(data, entities):
    st.header("📊 Extraction Overview")
    
    # Summary metrics
    col1, col2, col3, col4 = st.columns(4)
    
    with col1:
        st.metric("📄 Transcripts Processed", len(data.get('processed_files', [])))
    with col2:
        st.metric("🎯 Domains Found", len(entities['domains']))
    with col3:
        st.metric("🔬 Constructs Identified", len(entities['constructs']))
    with col4:
        st.metric("🧪 Assessments Extracted", len(entities['assessments']))
    
    col5, col6, col7, col8 = st.columns(4)
    with col5:
        st.metric("💊 Interventions Found", len(entities['interventions']))
    with col6:
        st.metric("⚙️ Technologies Identified", len(entities['technologies']))
    with col7:
        st.metric("📏 Metrics Catalogued", len(entities['metrics']))
    with col8:
        success_rate = len([f for f in data.get('processed_files', []) if 'error' not in f])
        st.metric("✅ Success Rate", f"{success_rate}/{len(data.get('processed_files', []))}")
    
    # File processing summary
    st.subheader("📋 File Processing Summary")
    
    file_summary = []
    for file_data in data.get('processed_files', []):
        file_summary.append({
            'File': file_data.get('file_name', 'Unknown'),
            'Status': '❌ Error' if 'error' in file_data else '✅ Success',
            'Constructs': file_data.get('constructs_identified', 0),
            'Transcript Length': f"{file_data.get('transcript_length', 0):,} chars"
        })
    
    df_summary = pd.DataFrame(file_summary)
    st.dataframe(df_summary, use_container_width=True)
    
    # Domain distribution chart
    st.subheader("📊 Domain Distribution")
    if entities['domains']:
        domain_counts = {domain: len(data['files']) for domain, data in entities['domains'].items()}
        fig = px.bar(
            x=list(domain_counts.keys()),
            y=list(domain_counts.values()),
            title="Number of Transcripts per Domain",
            labels={'x': 'Domain', 'y': 'Number of Transcripts'}
        )
        st.plotly_chart(fig, use_container_width=True)

def show_by_transcript(data):
    st.header("📄 Transcript-by-Transcript View")
    
    # File selector
    files = [f.get('file_name', 'Unknown') for f in data.get('processed_files', [])]
    selected_file = st.selectbox("Select a transcript:", files)
    
    # Find selected file data
    file_data = None
    for f in data.get('processed_files', []):
        if f.get('file_name') == selected_file:
            file_data = f
            break
    
    if file_data and 'error' not in file_data:
        # File info
        col1, col2, col3 = st.columns(3)
        with col1:
            st.metric("📊 Constructs Identified", file_data.get('constructs_identified', 0))
        with col2:
            st.metric("📝 Transcript Length", f"{file_data.get('transcript_length', 0):,} chars")
        with col3:
            practitioner_name = selected_file.replace('.txt', '').replace('_', ' ').title()
            st.info(f"👨‍⚕️ **Practitioner:** {practitioner_name}")
        
        # Domains and constructs
        domains_constructs = file_data.get('domains_constructs', {})
        
        st.subheader("🎯 Domains")
        for domain in domains_constructs.get('practitioner_domains', []):
            with st.expander(f"🎯 {domain.get('domain_name', 'Unknown Domain')}"):
                st.write("**Description:**", domain.get('domain_description', 'No description'))
                if domain.get('specialization_notes'):
                    st.write("**Specialization Notes:**", domain.get('specialization_notes'))
        
        st.subheader("🔬 Constructs")
        for construct in domains_constructs.get('constructs_mentioned', []):
            with st.expander(f"🔬 {construct.get('construct_name', 'Unknown Construct')}"):
                st.write("**Description:**", construct.get('construct_description', 'No description'))
                if construct.get('domain_association'):
                    st.write("**Domain:**", construct.get('domain_association'))
                if construct.get('assessment_context'):
                    st.write("**Assessment Context:**", construct.get('assessment_context'))
        
        # Assessments
        st.subheader("🧪 Assessments")
        assessments = file_data.get('assessments', {}).get('assessments', [])
        for assessment in assessments:
            with st.expander(f"🧪 {assessment.get('assessment_name', 'Unknown Assessment')}"):
                col1, col2 = st.columns(2)
                with col1:
                    st.write("**Description:**", assessment.get('assessment_description', 'No description'))
                    st.write("**Modality:**", assessment.get('modality', 'Unknown'))
                    if assessment.get('constructs_measured'):
                        st.write("**Constructs Measured:**", ', '.join(assessment.get('constructs_measured', [])))
                
                with col2:
                    tech = assessment.get('technology_vendor', {})
                    if tech.get('name'):
                        st.write("**Technology:**", tech.get('name'))
                        st.write("**Type:**", tech.get('type', 'Unknown'))
                        if tech.get('specific_equipment'):
                            st.write("**Equipment:**", tech.get('specific_equipment'))
                
                # Metrics
                metrics = assessment.get('metrics', [])
                if metrics:
                    st.write("**Metrics:**")
                    for metric in metrics:
                        metric_info = f"• **{metric.get('metric_name', 'Unknown')}**"
                        if metric.get('unit'):
                            metric_info += f" ({metric.get('unit')})"
                        if metric.get('reference_ranges'):
                            metric_info += f" - Range: {metric.get('reference_ranges')}"
                        st.markdown(metric_info)
        
        # Interventions
        st.subheader("💊 Interventions")
        interventions = file_data.get('interventions', {}).get('interventions', [])
        for intervention in interventions:
            with st.expander(f"💊 {intervention.get('intervention_name', 'Unknown Intervention')}"):
                st.write("**Description:**", intervention.get('intervention_description', 'No description'))
                if intervention.get('purpose'):
                    st.write("**Purpose:**", intervention.get('purpose'))
                if intervention.get('constructs_targeted'):
                    st.write("**Targets:**", ', '.join(intervention.get('constructs_targeted', [])))
                if intervention.get('intervention_types'):
                    st.write("**Types:**", ', '.join(intervention.get('intervention_types', [])))
    
    elif file_data:
        st.error(f"❌ Error processing this file: {file_data.get('error', 'Unknown error')}")

def show_domains(entities):
    st.header("🎯 Domains Overview")
    
    for domain_name, domain_data in entities['domains'].items():
        with st.expander(f"🎯 {domain_name} ({len(domain_data['files'])} transcripts)"):
            st.write("**Description:**", domain_data['description'])
            st.write("**Found in transcripts:**", ', '.join(set(domain_data['files'])))
            
            if domain_data['specialization_notes']:
                st.write("**Specialization Notes:**")
                for note in set(domain_data['specialization_notes']):
                    if note.strip():
                        st.write(f"• {note}")

def show_constructs(entities):
    st.header("🔬 Constructs Overview")
    
    # Filter by domain
    all_domains = list(entities['domains'].keys())
    selected_domain = st.selectbox("Filter by domain:", ['All'] + all_domains)
    
    filtered_constructs = entities['constructs']
    if selected_domain != 'All':
        filtered_constructs = {
            name: data for name, data in entities['constructs'].items()
            if data['domain_association'] == selected_domain
        }
    
    for construct_name, construct_data in filtered_constructs.items():
        with st.expander(f"🔬 {construct_name} ({len(construct_data['files'])} transcripts)"):
            st.write("**Description:**", construct_data['description'])
            if construct_data['domain_association']:
                st.write("**Domain:**", construct_data['domain_association'])
            st.write("**Found in transcripts:**", ', '.join(set(construct_data['files'])))

def show_assessments(entities):
    st.header("🧪 Assessments Overview")
    
    # Filter by modality
    all_modalities = list(set(data['modality'] for data in entities['assessments'].values() if data['modality']))
    selected_modality = st.selectbox("Filter by modality:", ['All'] + all_modalities)
    
    filtered_assessments = entities['assessments']
    if selected_modality != 'All':
        filtered_assessments = {
            name: data for name, data in entities['assessments'].items()
            if data['modality'] == selected_modality
        }
    
    for assessment_name, assessment_data in filtered_assessments.items():
        with st.expander(f"🧪 {assessment_name}"):
            col1, col2 = st.columns(2)
            
            with col1:
                st.write("**Description:**", assessment_data['description'])
                st.write("**Modality:**", assessment_data['modality'])
                if assessment_data['constructs_measured']:
                    st.write("**Measures:**", ', '.join(assessment_data['constructs_measured']))
            
            with col2:
                st.write("**Found in transcripts:**", ', '.join(set(assessment_data['files'])))
                
                if assessment_data['technologies']:
                    st.write("**Technologies Used:**")
                    for tech in assessment_data['technologies']:
                        st.write(f"• {tech.get('name', 'Unknown')} ({tech.get('type', 'Unknown type')})")
                
                if assessment_data['metrics']:
                    st.write("**Metrics:**")
                    for metric in assessment_data['metrics']:
                        metric_text = f"• {metric.get('metric_name', 'Unknown')}"
                        if metric.get('unit'):
                            metric_text += f" ({metric.get('unit')})"
                        st.write(metric_text)

def show_interventions(entities):
    st.header("💊 Interventions Overview")
    
    for intervention_name, intervention_data in entities['interventions'].items():
        with st.expander(f"💊 {intervention_name}"):
            st.write("**Description:**", intervention_data['description'])
            if intervention_data['purpose']:
                st.write("**Purpose:**", intervention_data['purpose'])
            if intervention_data['constructs_targeted']:
                st.write("**Targets:**", ', '.join(intervention_data['constructs_targeted']))
            if intervention_data['intervention_types']:
                st.write("**Types:**", ', '.join(intervention_data['intervention_types']))
            st.write("**Found in transcripts:**", ', '.join(set(intervention_data['files'])))

def show_technologies(entities):
    st.header("⚙️ Technologies Overview")
    
    for tech_name, tech_data in entities['technologies'].items():
        with st.expander(f"⚙️ {tech_name}"):
            col1, col2 = st.columns(2)
            
            with col1:
                st.write("**Type:**", tech_data['type'])
                if tech_data['equipment']:
                    st.write("**Equipment:**", tech_data['equipment'])
            
            with col2:
                st.write("**Used in assessments:**", ', '.join(set(tech_data['used_in_assessments'])))
                st.write("**Found in transcripts:**", ', '.join(set(tech_data['files'])))

def show_metrics(entities):
    st.header("📏 Metrics Overview")
    
    for metric_name, metric_data in entities['metrics'].items():
        with st.expander(f"📏 {metric_name}"):
            col1, col2 = st.columns(2)
            
            with col1:
                if metric_data['unit']:
                    st.write("**Unit:**", metric_data['unit'])
                if metric_data['reference_ranges']:
                    st.write("**Reference Ranges:**", metric_data['reference_ranges'])
                if metric_data['validity_confidence']:
                    st.write("**Validity:**", metric_data['validity_confidence'])
            
            with col2:
                st.write("**Used in assessments:**", ', '.join(set(metric_data['used_in_assessments'])))
                st.write("**Found in transcripts:**", ', '.join(set(metric_data['files'])))

if __name__ == "__main__":
    main()