# diagnostic_analysis.py - Add this to your project root to analyze transcript content

import json
from pathlib import Path
import anthropic
import os

def analyze_transcript_content(file_path):
    """Analyze what's actually in the transcript"""
    
    with open(file_path, 'r', encoding='utf-8') as f:
        content = f.read()
    
    print(f"\n📄 ANALYZING: {file_path.name}")
    print(f"📊 Length: {len(content)} characters")
    print(f"📝 First 500 characters:")
    print("-" * 50)
    print(content[:500])
    print("-" * 50)
    
    # Simple keyword search
    assessment_keywords = ['test', 'assessment', 'measure', 'evaluate', 'scan', 'blood', 'analysis', 'monitoring']
    technology_keywords = ['device', 'software', 'equipment', 'platform', 'system', 'tool', 'app', 'machine']
    intervention_keywords = ['treatment', 'therapy', 'program', 'intervention', 'protocol', 'exercise', 'training']
    
    print(f"\n🔍 KEYWORD ANALYSIS:")
    for category, keywords in [("Assessments", assessment_keywords), 
                              ("Technologies", technology_keywords), 
                              ("Interventions", intervention_keywords)]:
        found = [kw for kw in keywords if kw.lower() in content.lower()]
        print(f"{category}: {found}")
    
    return content

def llm_content_analysis(content, api_key):
    """Use LLM to analyze what types of content are present"""
    
    client = anthropic.Anthropic(api_key=api_key)
    
    prompt = f"""
    Analyze this transcript and tell me what types of content it contains:

    TRANSCRIPT (first 2000 chars):
    {content[:2000]}

    Answer these questions:
    1. What type of conversation is this? (interview, consultation, meeting, notes, etc.)
    2. What is the speaker's role/profession?
    3. Does this contain health/performance assessment methods?
    4. Does this mention any testing, measurement, or evaluation procedures?
    5. Does this mention any technologies, devices, or tools?
    6. Does this mention any treatments, interventions, or programs?
    7. Is this formatted as an interview transcript or something else?

    Provide a brief analysis of what content is actually present.
    """
    
    try:
        response = client.messages.create(
            model="claude-sonnet-4-20250514",
            max_tokens=1000,
            messages=[{"role": "user", "content": prompt}]
        )
        return response.content[0].text
    except Exception as e:
        return f"Analysis failed: {e}"

def main():
    print("🔍 TRANSCRIPT CONTENT DIAGNOSTIC")
    print("=" * 50)
    
    # Get API key
    api_key = os.getenv('ANTHROPIC_API_KEY')
    if not api_key:
        env_file = Path('.env')
        if env_file.exists():
            with open(env_file, 'r') as f:
                for line in f:
                    if line.startswith('ANTHROPIC_API_KEY='):
                        api_key = line.split('=', 1)[1].strip()
                        break
    
    transcript_folder = Path("data/transcripts")
    transcript_files = list(transcript_folder.glob("*.txt"))
    
    for file_path in transcript_files:
        # Basic analysis
        content = analyze_transcript_content(file_path)
        
        # LLM analysis if API key available
        if api_key:
            print(f"\n🤖 LLM ANALYSIS:")
            analysis = llm_content_analysis(content, api_key)
            print(analysis)
        
        print("\n" + "="*80)

if __name__ == "__main__":
    main()