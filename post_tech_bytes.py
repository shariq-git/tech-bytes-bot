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
    now = datetime.datetime.now()
    day_name = now.strftime("%A")
    
    themes = {
        "Monday": "Cloud Infrastructure Trivia (AWS/Azure/K8s)",
        "Tuesday": "AI Hardware & GPU Scaling (2026 Chips)",
        "Wednesday": "Networking & Security(firewalls,ip rules etc) ",
        "Thursday": "Open Source & Linux History",
        "Friday": "SRE Humor: Outages, On-call, and 'DNS is always the culprit'",
        "Saturday": "Future Tech & 2027 Roadmaps"
    }
    current_theme = themes.get(day_name, "General DevOps Insights")

    # Fetch RSS for context
    articles = []
    for url in RSS_FEEDS:
        try:
            feed = feedparser.parse(url)
            for entry in feed.entries[:3]:
                articles.append(entry.title)
        except:
            continue
    
    trend_context = ""
    if articles:
        selected = random.sample(articles, min(3, len(articles)))
        trend_context = "Latest Industry Context:\n" + "\n".join([f"- {t}" for t in selected])

    prompt = f"""
    Context: You are a Senior SRE with 6+ years of experience and a touch of professional wit.
    Current Date: {now.strftime('%Y-%m-%d')}
    Theme: {current_theme}
    {trend_context}

    Task: Write a high-impact LinkedIn post titled '🚀 Tech Bytes'.

    Visual & Formatting Rules (STRICT):
    1. **Hook**: Start with a **bold, punchy opening hook** that stops the scroll.
    2. **Spacing**: Use **double-line breaks** between points. Whitespace is critical!
    3. **Bullets**: Use **🔹 or ⚡ emojis** exclusively as bullet points.
    4. **Emphasis**: **Bold** all technical terms, version numbers, or metrics (e.g., **Kubernetes v1.35**, **99.9% Uptime**).
    5. **The 2026 Factor**: Reference a futuristic but realistic tech milestone.
    6. Content: 2-3 "Did you know?" facts or insights relevant to 2026.
    7. Friday Rule: Use professional sarcasm/humor about SRE life.
    8. Add some interview question with answer on technolgies like linux,AWS,AZURE,Networking,Kubernetes ,SRE etc
    STRICT NARRATIVE RULES:
    1. NO FIRST-PERSON: Never use "I", "me", "my", or "we". 
    2. NO FALSE STORIES: Do not invent stories about "projects I worked on" or "incidents I handled".
    3. PURE OBSERVATION: Focus on universal engineering truths, fun facts, and objective 2026 tech trends.
    4. HUMOR STYLE: Use observational wit (e.g., "The industry still runs on...") rather than personal stories.

    Hashtags: Exactly 5 (#TechBytes #SRE #DevOps #CloudNative #2026Tech)
    Timestamp: 🕒 2026 Insights | {now.strftime('%H:%M')} IST
    """

    response = client.models.generate_content(model="gemini-3.1-flash-lite", contents=prompt)
    return response.text.strip()

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
        print(f"Status: {res.status_code}")
        if res.status_code not in [200, 201]:
            print(res.text)
            sys.exit(1)
