import os
import requests
import datetime
import sys
import random
import time
import json
import feedparser
from google import genai

# =========================
# CONFIG & ENV
# =========================
L_TOKEN = os.environ.get("LINKEDIN_TOKEN")
L_AUTH_ID = os.environ.get("LINKEDIN_AUTHOR_ID")
GEM_KEY = os.environ.get("GEMINI_API_KEY")

RSS_FEEDS = [
    "https://thenewstack.io/feed/",
    "https://aws.amazon.com/blogs/aws/feed/",
    "https://azure.microsoft.com/en-us/blog/feed/",
    "https://cloud.google.com/blog/products/containers-kubernetes/rss/",
    "https://kubernetes.io/feed.xml",
    "https://www.datadoghq.com/blog/rss/"
]

# =========================
# CONTENT LOGIC
# =========================
def get_gemini_content():
    if not GEM_KEY:
        raise ValueError("Missing GEMINI_API_KEY")

    # Use v1beta to ensure all model versions are accessible
    client = genai.Client(api_key=GEM_KEY, http_options={'api_version': 'v1beta'})
    
    ist_offset = datetime.timezone(datetime.timedelta(hours=5, minutes=30))
    now = datetime.datetime.now(ist_offset)
    day_name = now.strftime("%A")
    
    themes = {
        "Monday": "Cloud Infrastructure & High Availability",
        "Tuesday": "AI Hardware & GPU Scaling (2026 Chips)",
        "Wednesday": "Azure & Networking (AKS, Entra ID, Security)",
        "Thursday": "Open Source & Linux Kernel Internals",
        "Friday": "SRE Humor & Production Lessons",
        "Saturday": "Future Tech Roadmaps"
    }
    current_theme = themes.get(day_name, "General DevOps Insights")

    articles = []
    for url in RSS_FEEDS:
        try:
            feed = feedparser.parse(url)
            for entry in feed.entries[:3]:
                articles.append(entry.title)
        except: continue
    
    trend_context = "LATEST NEWS CONTEXT:\n" + "\n".join(random.sample(articles, min(3, len(articles)))) if articles else ""

    prompt = f"""
    CONTEXT: Senior SRE Expert.
    CURRENT DAY: {day_name}
    THEME: {current_theme}
    {trend_context}

    TASK: Write a LinkedIn post titled '🚀 TECH BYTES: THE {day_name.upper()} SRE PULSE'.

    NARRATIVE RULES:
    1. NO FIRST-PERSON: Do NOT use "I", "me", or "my".
    2. NO FALSE STORIES: Do not invent anecdotes.
    3. THEME LOCK: Today is {day_name}.

    VISUAL FORMATTING (STRICT - NO MARKDOWN):
    1. NO ASTERISKS: Do NOT use ** for bolding.
    2. PUNCHY HOOK: Start with an ALL-CAPS opening sentence.
    3. TERMINAL STYLE: Use ──▶ for bullet points.
    4. SEPARATOR: Use ━━━━━━.
    5. WHITESPACE: Double-line breaks between every point.

    HASHTAGS: Exactly 5 (#TechBytes #SRE #DevOps #CloudNative #2026Tech)
    """

    # --- MULTI-MODEL FALLBACK LOGIC ---
    # We try Flash 1.5 first (most stable), then 2.0 (latest), then 8B (fastest fallback)
    models_to_try = ["gemini-1.5-flash", "gemini-2.0-flash", "gemini-1.5-flash-8b"]
    response_text = ""

    for model_id in models_to_try:
        try:
            print(f"[INFO] Attempting generation with {model_id}...")
            response = client.models.generate_content(model=model_id, contents=prompt)
            if response and response.text:
                response_text = response.text
                print(f"[SUCCESS] Content generated using {model_id}")
                break
        except Exception as e:
            print(f"[WARN] {model_id} failed: {e}")
            continue # Try next model in list

    if not response_text:
        raise RuntimeError("CRITICAL: All Gemini models failed to generate content.")

    # SRE Sanitizer: Final guardrail to remove any stray asterisks
    clean_content = response_text.replace("**", "").replace("*", "").strip()
    return clean_content

def post_to_linkedin(content):
    content_to_post = os.environ.get("POST_CONTENT", content)
    if not content_to_post:
        print("[ERROR] No content found to post.")
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
    return requests.post(url, headers=headers, json=data, timeout=15)

if __name__ == "__main__":
    mode = sys.argv[1] if len(sys.argv) > 1 else "propose"
    try:
        if mode == "propose":
            print(get_gemini_content())
            
        elif mode == "post":
            # 1. Grab content from the environment (passed from GHA needs.generate)
            content_from_env = os.environ.get("POST_CONTENT")
            
            # 2. Check if it actually exists before calling the API
            if not content_from_env or content_from_env.strip() == "":
                print("[FATAL] POST_CONTENT environment variable is empty!")
                sys.exit(1)
            
            # 3. Pass the valid content
            res = post_to_linkedin(content_from_env)
            
            if res:
                print(f"[INFO] LinkedIn Response Status: {res.status_code}")
                if res.status_code != 201:
                    print(f"[DEBUG] Full Response: {res.text}")
                    sys.exit(1) # Ensure the pipeline fails if LinkedIn rejects the post
                    
    except Exception as e:
        print(f"[FATAL] Script failed: {e}")
        sys.exit(1)
