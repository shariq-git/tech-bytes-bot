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

    log("Initializing Gemini client...")

    client = genai.Client(api_key=GEM_KEY)

    ist_offset = datetime.timezone(datetime.timedelta(hours=5, minutes=30))
    now = datetime.datetime.now(ist_offset)

    day_name = now.strftime("%A")

    themes = {
        "Monday": "Cloud Infrastructure & High Availability",
        "Tuesday": "AI Hardware & GPU Scaling",
        "Wednesday": "Azure Networking & Security",
        "Thursday": "Open Source & Linux Internals",
        "Friday": "SRE Humor & Production Lessons",
        "Saturday": "Future Tech Roadmaps",
        "Sunday": "Platform Engineering & Automation"
    }

    current_theme = themes.get(day_name, "General DevOps Insights")

    # =========================
    # FETCH RSS ARTICLES
    # =========================

    log("Fetching RSS feeds...")

    articles = []

    for url in RSS_FEEDS:
        try:
            feed = feedparser.parse(url)

            if not feed.entries:
                warn(f"No entries found in {url}")
                continue

            for entry in feed.entries[:3]:
                title = getattr(entry, "title", "").strip()

                if title:
                    articles.append(title)

        except Exception as e:
            warn(f"RSS feed failed: {url} | {e}")

    sampled_articles = []

    if articles:
        sampled_articles = random.sample(
            articles,
            min(3, len(articles))
        )

    trend_context = "\n".join(sampled_articles)

    # =========================
    # PROMPT
    # =========================

    prompt = f"""
CONTEXT:
You are a senior SRE and cloud infrastructure expert.

CURRENT DAY:
{day_name}

TODAY'S THEME:
{current_theme}

LATEST TECH CONTEXT:
{trend_context}

TASK:
Write a professional LinkedIn post titled:

🚀 TECH BYTES: THE {day_name.upper()} SRE PULSE

STRICT RULES:
- No markdown
- No asterisks
- No fake stories
- No first-person language
- No emojis except the title emoji
- Keep it concise and engaging
- Use terminal-style bullets: ──▶
- Use separator: ━━━━━━
- Add spacing between sections
- Tone should feel like a senior infrastructure engineer

ENDING:
Exactly 5 hashtags:
#TechBytes #SRE #DevOps #CloudNative #2026Tech
"""

    # =========================
    # MODEL FALLBACKS
    # =========================

    models_to_try = [
        "gemini-2.5-flash",
        "gemini-2.0-flash",
        "gemini-1.5-flash"
    ]

    response_text = None

    for model_id in models_to_try:

        try:
            log(f"Trying model: {model_id}")

            response = client.models.generate_content(
                model=model_id,
                contents=prompt
            )

            if response and response.text:
                response_text = response.text.strip()

                log(f"Success using {model_id}")
                break

            warn(f"Empty response from {model_id}")

        except Exception as e:
            warn(f"{model_id} failed: {e}")
            time.sleep(2)

    if not response_text:
        raise RuntimeError("All Gemini models failed")

    # =========================
    # FINAL SANITIZATION
    # =========================

    clean_content = (
        response_text
        .replace("*", "")
        .strip()
    )

    if len(clean_content) < 50:
        raise RuntimeError("Generated content too short")

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
