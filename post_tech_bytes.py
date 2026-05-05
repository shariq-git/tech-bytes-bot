import os
import requests
import datetime
import sys
import random
from google import genai

# Load secrets from GitHub Environment
L_TOKEN = os.environ.get('LINKEDIN_TOKEN')
L_AUTH_ID = os.environ.get('LINKEDIN_AUTHOR_ID')
GEM_KEY = os.environ.get('GEMINI_API_KEY')

def get_gemini_content():
    """Generates unique, randomized SRE content based on the day of the week."""
    client = genai.Client(api_key=GEM_KEY)
    now = datetime.datetime.now()
    day_name = now.strftime("%A")
    
    # Unique seed ensures the AI doesn't repeat scenarios
    random_seed = now.strftime("%Y%m%d%H%M")
    
    # 6-Day Professional Schedule
    themes = {
        "Monday": "Deep Dive: Advanced Kubernetes & Container Orchestration (Infra Focus)",
        "Tuesday": "AWS Architecture & Scalability (EKS, Networking, Storage)",
        "Wednesday": "Azure Infra & Reliability (AKS, Entra ID)",
        "Thursday": "Infrastructure as Code (Terraform & OpenTofu)",
        "Friday": "Observability & SRE Toil Reduction (eBPF, OpenTelemetry, Datadog, ELK, Grafana)",
        "Saturday": "Senior SRE/DevOps Interview Prep (Scenario-based questions)"
    }

    current_theme = themes.get(day_name, "General DevOps & Platform Engineering")

    prompt = f"""
System: You are a Senior SRE with 6+ years of hands-on production experience in cloud-native systems.

Current Date: {now.strftime('%Y-%m-%d')}
Seed ID: {random_seed}

Task: Write a high-impact LinkedIn post titled '🚀 Tech Bytes'.

Focus Area: {current_theme}

Content Requirements:

1. Structure:
   - Start with a strong hook
   - Real-world scenario (no generic explanations)
   - Clear solution with technical depth
   - End with takeaway

2. Day-specific rules:
   - Mon–Fri → Problem → Investigation → Solution
   - Saturday → 3 interview questions + pro-tips

3. Technical Depth:
   - Use 2025–2026 practices (Gateway API, eBPF, Zero Trust)

4. Style:
   - Concise, human, slightly opinionated
   - Avoid textbook tone

5. Timestamp:
   🕒 2026 Insights | {now.strftime('%H:%M')} IST

6. Hashtags:
   - Exactly 5 (#TechBytes #SRE #DevOps + 2 relevant)

Goal:
Real Senior SRE vibe — not AI-generated.
"""

    response = client.models.generate_content(
        model="gemini-2.5-flash",   # safer/stable model
        contents=prompt
    )

    return response.text.strip()


def post_to_linkedin(content):
    """Publishes the generated content to LinkedIn via UGC API."""
    
    content_to_post = os.environ.get('POST_CONTENT', content)
    
    if not content_to_post:
        print("Error: No content found to post.")
        return None

    url = "https://api.linkedin.com/v2/ugcPosts"
    headers = {
        "Authorization": f"Bearer {L_TOKEN}",
        "Content-Type": "application/json",
        "X-Restli-Protocol-Version": "2.0.0"
    }
    
    data = {
        "author": L_AUTH_ID,
        "lifecycleState": "PUBLISHED",
        "specificContent": {
            "com.linkedin.ugc.ShareContent": {
                "shareCommentary": {"text": content_to_post},
                "shareMediaCategory": "NONE"
            }
        },
        "visibility": {"com.linkedin.ugc.MemberNetworkVisibility": "PUBLIC"}
    }

    return requests.post(url, headers=headers, json=data)


if __name__ == "__main__":
    mode = sys.argv[1] if len(sys.argv) > 1 else "propose"
    
    if mode == "propose":
        final_content = get_gemini_content()
        print(final_content)

    elif mode == "post":
        res = post_to_linkedin("")
        if res:
            print(f"LinkedIn Status Code: {res.status_code}")
            if res.status_code != 201:
                print(f"Response: {res.text}")
