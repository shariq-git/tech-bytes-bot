import os
import requests
import datetime
import sys
import random
import time
from google import genai

# Load secrets from GitHub Environment
L_TOKEN = os.environ.get('LINKEDIN_TOKEN')
L_AUTH_ID = os.environ.get('LINKEDIN_AUTHOR_ID')
GEM_KEY = os.environ.get('GEMINI_API_KEY')

# =========================
# Dynamic Content Pools
# =========================

themes = {
    "Monday": [
        "Cloud Infrastructure Trivia",
        "Kubernetes Scaling Stories",
        "AWS Architecture Secrets",
        "Container Runtime Facts",
        "Platform Engineering Trends"
    ],

    "Tuesday": [
        "AI Infrastructure",
        "GPU Clusters",
        "TPUs & AI Accelerators",
        "LLM Scaling",
        "AI Datacenter Evolution"
    ],

    "Wednesday": [
        "Zero Trust Security",
        "Quantum Cryptography",
        "Cloud Networking",
        "Service Mesh Security",
        "Identity Federation"
    ],

    "Thursday": [
        "Linux Kernel Trivia",
        "Open Source History",
        "eBPF Insights",
        "Unix Engineering Stories",
        "Infrastructure Evolution"
    ],

    "Friday": [
        "SRE Humor",
        "Production Nightmares",
        "DevOps Lessons",
        "Famous Engineering Failures",
        "PagerDuty Chaos"
    ],

    "Saturday": [
        "Future Tech",
        "Edge Computing",
        "Web3 Infrastructure",
        "2026 Cloud Trends",
        "Autonomous AI Systems"
    ]
}

hooks = [
    "🚀 Engineering is wild...",
    "⚡ Did you know?",
    "🔥 One tiny config can take down an entire platform.",
    "💀 Every SRE has at least one DNS horror story.",
    "🔍 Modern infrastructure is way more fragile than people think."
]

tech_context = [
    "Kubernetes v1.35",
    "eBPF observability",
    "Zero-Trust networking",
    "AI-native infrastructure",
    "WASM workloads",
    "Gateway API adoption",
    "liquid cooling datacenters"
]

# =========================
# Retry Logic
# =========================

def generate_with_retry(client, prompt, retries=5):

    models = [
        "gemini-2.5-flash",
        "gemini-1.5-flash"
    ]

    for model in models:

        for attempt in range(retries):

            try:

                print(f"[INFO] Using model: {model}")
                print(f"[INFO] Attempt: {attempt + 1}")

                response = client.models.generate_content(
                    model=model,
                    contents=prompt
                )

                if not response or not response.text:
                    raise ValueError("Empty Gemini response")

                return response.text.strip()

            except Exception as e:

                print(f"[WARN] {model} failed: {e}")

                if "503" in str(e) or "UNAVAILABLE" in str(e):

                    sleep_time = 2 ** attempt
                    print(f"[INFO] Retrying in {sleep_time}s...")
                    time.sleep(sleep_time)

                else:
                    break

    raise RuntimeError("All Gemini retries failed")

# =========================
# Content Generation
# =========================

def get_gemini_content():

    if not GEM_KEY:
        raise ValueError("GEMINI_API_KEY missing")

    client = genai.Client(api_key=GEM_KEY)

    now = datetime.datetime.now()
    day_name = now.strftime("%A")

    selected_theme = random.choice(
        themes.get(day_name, ["General Tech"])
    )

    selected_hook = random.choice(hooks)

    selected_context = random.choice(tech_context)

    print(f"[INFO] Day: {day_name}")
    print(f"[INFO] Theme: {selected_theme}")

    prompt = f"""
Context:
You are a highly experienced Senior SRE/DevOps engineer.

Task:
Write a LinkedIn post titled:

🚀 Tech Bytes

Theme:
{selected_theme}

Tech Context:
{selected_context}

Writing Rules:

1. Start with this hook:
{selected_hook}

2. Style:
- Short
- Conversational
- Human sounding
- Insightful
- Slightly witty

3. Structure:
- 1 strong opening line
- 2-3 short bullet points
- Easy to scan
- No walls of text

4. Content:
- Include surprising engineering facts,
production lessons,
or modern 2026 infrastructure insights.

5. Mention at least one:
- Kubernetes trend
- AI infra trend
- Cloud scalability fact
- Security evolution
- Datacenter innovation

6. Friday posts should include SRE humor.

7. Keep total length under 120 words.

8. Do NOT sound AI-generated.

9. End with a short engaging question.

10. Exactly 5 hashtags.

Mandatory hashtags:
#TechBytes #SRE #DevOps

The remaining hashtags should match the topic naturally.
"""

    return generate_with_retry(client, prompt)

# =========================
# LinkedIn Posting
# =========================

def post_to_linkedin(content):

    content_to_post = os.environ.get('POST_CONTENT', content)

    if not content_to_post:
        print("Error: No content found to post.")
        return None

    print("[INFO] Posting to LinkedIn...")
    print(f"[INFO] Content Length: {len(content_to_post)}")

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
                "shareCommentary": {
                    "text": content_to_post
                },
                "shareMediaCategory": "NONE"
            }
        },
        "visibility": {
            "com.linkedin.ugc.MemberNetworkVisibility": "PUBLIC"
        }
    }

    return requests.post(
        url,
        headers=headers,
        json=data,
        timeout=15
    )

# =========================
# Main
# =========================

if __name__ == "__main__":

    # Random startup jitter
    time.sleep(random.randint(2, 8))

    mode = sys.argv[1] if len(sys.argv) > 1 else "propose"

    try:

        if mode == "propose":

            print("[INFO] Generating content...")

            final_content = get_gemini_content()

            print(final_content)

        elif mode == "post":

            print("[INFO] Publishing to LinkedIn...")

            res = post_to_linkedin("")

            if res:

                print(f"LinkedIn Status Code: {res.status_code}")

                if res.status_code != 201:
                    print(f"Response: {res.text}")
                    sys.exit(1)

                print("[SUCCESS] LinkedIn post published")

    except Exception as e:

        print(f"[FATAL] {e}")

        sys.exit(1)
