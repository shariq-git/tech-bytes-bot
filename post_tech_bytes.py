import os
import datetime
import random
from google import genai

def get_gemini_content():
    client = genai.Client(api_key=os.environ.get('GEMINI_API_KEY'))
    now = datetime.datetime.now()
    day_name = now.strftime("%A")
    
    # 1. Create a unique seed based on the exact minute to ensure total randomness
    random_seed = now.strftime("%Y%m%d%H%M")
    
    # 2. Define the Daily Theme (Broad categories to allow AI creativity)
    themes = {
        "Monday": "Advanced Kubernetes & Container Orchestration",
        "Tuesday": "AWS Cloud Architecture & Scaling",
        "Wednesday": "Azure Infrastructure & Enterprise Security",
        "Thursday": "Infrastructure as Code (Terraform & OpenTofu)",
        "Friday": "Observability, Monitoring & SRE Toil Reduction",
        "Saturday": "Senior SRE/DevOps Interview Scenarios"
    }
    
    current_theme = themes.get(day_name, "DevOps Engineering")

    # 3. The "Freshness" Prompt
    # We instruct the AI to invent a unique, specific problem every time.
    prompt = f"""
    Seed ID: {random_seed}
    Current Date: {now.strftime('%Y-%m-%d')}
    Role: Senior SRE/DevOps Architect (6+ years experience).
    
    Task: Write a LinkedIn post titled '🚀 Tech Bytes' for {day_name}.
    Daily Theme: {current_theme}.
    
    CRITICAL INSTRUCTION FOR FRESHNESS:
    - Do NOT provide a generic overview. 
    - Invent a HIGHLY SPECIFIC, complex technical 'Problem' related to {current_theme} that an engineer might face in 2026.
    - Provide a 'Solution' using modern engineering patterns (e.g., eBPF, GitOps, Platform Engineering, Zero-Trust).
    - Ensure this specific scenario has not been used in previous 'Tech Bytes' posts.
    
    Format:
    1. Catchy hook.
    2. The Problem (The Hurdle).
    3. The Solution (The Deep Dive).
    4. Why it matters for SREs.
    5. Timestamp: 🕒 2026 Live Lab | {now.strftime('%H:%M')} IST.
    6. Exactly 5 hashtags including #TechBytes #SRE #DevOps.
    """
    
    response = client.models.generate_content(model="gemini-3-flash-preview", contents=prompt)
    return response.text.strip()
