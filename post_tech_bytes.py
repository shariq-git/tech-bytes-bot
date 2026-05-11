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

    client = genai.Client(api_key=GEM_KEY)
    
    # 1. FORCE IST TIMEZONE (Fixes the Day Mismatch)
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

    # Fetch RSS for context
    articles = []
    for url in RSS_FEEDS:
        try:
            feed = feedparser.parse(url)
            for entry in feed.entries[:3]:
                articles.append(entry.title)
        except: continue
    
    trend_context = "LATEST NEWS CONTEXT:\n" + "\n".join(random.sample(articles, min(3, len(articles)))) if articles else ""

    # 2. THE VISUAL PROMPT (NO ASTERISKS)
    prompt = f"""
    CONTEXT: Senior SRE Expert.
    CURRENT DAY: {day_name}
    THEME: {current_theme}
    {trend_context}

    TASK: Write a LinkedIn post titled '🚀 TECH BYTES: THE {day_name.upper()} SRE PULSE'.

    NARRATIVE RULES:
    1. NO FIRST-PERSON: Do NOT use "I", "me", or "my". Focus on technical truths.
    2. NO FALSE STORIES: Do not invent personal anecdotes.
    3. THEME LOCK: Today is {day_name}. Only mention Friday if today is actually Friday.

    VISUAL FORMATTING (STRICT - NO MARKDOWN):
    1. NO ASTERISKS: Do NOT use ** for bolding. It breaks the visual.
    2. PUNCHY HOOK: Start with an ALL-CAPS opening sentence.
    3. TERMINAL STYLE: Use ──▶ for bullet points.
    4. SEPARATOR: Use a line of ━━━━━━ to separate the title from content.
    5. WHITESPACE: Double-line breaks between every single point.

    STRUCTURE:
    - TITLE: 🚀 TECH BYTES: {day_name.upper()} EDITION
    ━━━━━━━━━━━━━━━━━━━━
    - HOOK (ALL-CAPS)
    - 2-3 TECHNICAL INSIGHTS (using ──▶)
    - 1 ENGAGEMENT QUESTION (ALL-CAPS)

    HASHTAGS: Exactly 5 (#TechBytes #SRE #DevOps #CloudNative #2026Tech)
    TIMESTAMP: 🕒 2026 INSIGHTS | {now.strftime('%H:%M')} IST
    """

    response = client.models.generate_content(model="gemini-1.5-flash", contents=prompt)
    
    # SRE Sanitizer: Final guardrail to remove any stray asterisks
    clean_content = response.text.replace("**", "").replace("*", "").strip()
    return clean_content

def post_to_linkedin(content):
    content_to_post = os.environ.get("POST_CONTENT", content)
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
    if mode == "propose":
        print(get_gemini_content())
    elif mode == "post":
        res = post_to_linkedin("")
        print(f"[INFO] LinkedIn Response Status: {res.status_code}")
