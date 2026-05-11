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
    """Generates short, engaging 2-3 liner fun facts and 2026 tech insights."""
    client = genai.Client(api_key=GEM_KEY)
    now = datetime.datetime.now()
    day_name = now.strftime("%A")
    
    # 6-Day Theme Logic for Variety
    themes = {
        "Monday": "Cloud Infrastructure Trivia (AWS/Azure/K8s)",
        "Tuesday": "AI & Large Language Model Hardware (GPUs/TPUs)",
        "Wednesday": "Networking & Security (Zero Trust, Quantum Cryptography)",
        "Thursday": "Open Source History & Linux Kernel fun facts",
        "Friday": "DevOps Culture & Famous Engineering Failures/Lessons",
        "Saturday": "Future Tech (Web3, Edge Computing, 2026 Trends)"
    }

    current_theme = themes.get(day_name, "General Tech Curiosities")

    prompt = f"""
    Context: You are a Senior SRE/DevOps professional.
    Task: Write a LinkedIn post titled '🚀 Tech Bytes'.
    
    Style: 
    - Short, snappy, and conversational.
    - Format: 1 Hook Sentence + 2-3 bullet points of mind-blowing fun facts or latest 2026 tech insights.
    - Must sound like a human expert sharing a "cool story" with colleagues, not a manual.
    
    Focus Area: {current_theme}
    Current Year: 2026

    Requirements:
    1. Hook: Start with something like "Did you know?" or "Engineering is wild..."
    2. Content: Provide 2-3 "Fun Facts" or "Did you know?" points related to {current_theme}.
    3. The "2026" Factor: Mention at least one tech milestone relevant to the current year (e.g., specific K8s versions, chip advancements, or sustainability in data centers).
    4. Length: Keep the total post under 100 words.
    5. Hashtags: Exactly 5 (#TechBytes #SRE #TechTrivia #Innovation #2026Tech)
    """

    response = client.models.generate_content(
        model="gemini-3-flash-preview", 
        contents=prompt
    )
    return response.text

    response = client.models.generate_content(
        model="gemini-3-flash-preview",   # safer/stable model
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
