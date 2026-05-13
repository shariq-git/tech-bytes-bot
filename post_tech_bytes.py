import os
import sys
import time
import random
import traceback
import datetime

import requests
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
# HELPERS
# =========================

def log(msg):
    print(f"[INFO] {msg}", flush=True)


def warn(msg):
    print(f"[WARN] {msg}", flush=True)


def fatal(msg):
    print(f"[FATAL] {msg}", flush=True)


# =========================
# GEMINI CONTENT GENERATION
# =========================

def get_gemini_content():
    if not GEM_KEY:
        raise ValueError("Missing GEMINI_API_KEY")

    client = genai.Client(
        api_key=GEM_KEY,
        http_options={'api_version': 'v1beta'}
    )

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

            if not feed.entries:
                continue

            for entry in feed.entries[:3]:
                articles.append(entry.title)

        except:
            continue

    trend_context = ""

    if articles:
        trend_context = (
            "LATEST NEWS CONTEXT:\n" +
            "\n".join(random.sample(articles, min(3, len(articles))))
        )

    prompt = f"""
CONTEXT: Senior SRE Expert.

CURRENT DAY: {day_name}

THEME: {current_theme}

{trend_context}

TASK:
Write a LinkedIn post titled:
'🚀 TECH BYTES: THE {day_name.upper()} SRE PULSE'

RULES:
1. NO FIRST PERSON
2. NO FAKE STORIES
3. NO MARKDOWN
4. NO ASTERISKS
5. Use ──▶ bullets
6. Use ━━━━━━ separator
7. Exactly 5 hashtags

HASHTAGS:
#TechBytes #SRE #DevOps #CloudNative #2026Tech
"""

    models_to_try = [
        "gemini-2.5-flash",
        "gemini-1.5-flash",
        "gemini-1.5-flash-8b"
    ]

    response_text = ""

    for model_id in models_to_try:
        try:
            response = client.models.generate_content(
                model=model_id,
                contents=prompt
            )

            if response and response.text:
                response_text = response.text
                break

        except:
            continue

    if not response_text:
        raise RuntimeError("All Gemini models failed.")

    clean_content = (
        response_text
        .replace("**", "")
        .replace("*", "")
        .strip()
    )

    return clean_content


# =========================
# LINKEDIN POSTING
# =========================

def post_to_linkedin(content):

    if not L_TOKEN:
        raise ValueError("Missing LINKEDIN_TOKEN")

    if not L_AUTH_ID:
        raise ValueError("Missing LINKEDIN_AUTHOR_ID")

    if not content:
        raise ValueError("No content to post")

    log("Publishing to LinkedIn...")

    url = "https://api.linkedin.com/v2/ugcPosts"

    headers = {
        "Authorization": f"Bearer {L_TOKEN}",
        "Content-Type": "application/json",
        "X-Restli-Protocol-Version": "2.0.0"
    }

    payload = {
        "author": L_AUTH_ID,
        "lifecycleState": "PUBLISHED",
        "specificContent": {
            "com.linkedin.ugc.ShareContent": {
                "shareCommentary": {
                    "text": content
                },
                "shareMediaCategory": "NONE"
            }
        },
        "visibility": {
            "com.linkedin.ugc.MemberNetworkVisibility": "PUBLIC"
        }
    }

    response = requests.post(
        url,
        headers=headers,
        json=payload,
        timeout=30
    )

    log(f"LinkedIn status code: {response.status_code}")

    if response.status_code not in [200, 201]:
        warn(f"LinkedIn API error: {response.text}")
        response.raise_for_status()

    return response


# =========================
# MAIN
# =========================

if __name__ == "__main__":

    mode = sys.argv[1] if len(sys.argv) > 1 else "propose"

    try:

        if mode == "propose":

            log("Generating content...")

            content = get_gemini_content()

            print(content)

        elif mode == "post":

            log("Reading generated content...")

            post_content = os.environ.get("POST_CONTENT")

            if not post_content or not post_content.strip():
                raise ValueError("POST_CONTENT is empty")

            response = post_to_linkedin(post_content)

            log("LinkedIn post published successfully")

            print(response.text)

        else:
            raise ValueError(f"Invalid mode: {mode}")

    except Exception as e:

        fatal(str(e))

        traceback.print_exc()

        sys.exit(1)
