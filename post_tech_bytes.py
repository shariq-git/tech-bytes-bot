import os
import requests
import datetime
import sys
from google import genai

# Load secrets from GitHub
L_TOKEN = os.environ.get('LINKEDIN_TOKEN')
L_AUTH_ID = os.environ.get('LINKEDIN_AUTHOR_ID')
GEM_KEY = os.environ.get('GEMINI_API_KEY')

def get_gemini_content():
    client = genai.Client(api_key=GEM_KEY)
    
    # Logic to pick topic based on day
    day = datetime.datetime.now().strftime("%A")
    # Modified to include specific 'Pain Points' for better engagement
    topic_map = {
        "Monday": "Kubernetes: Resource Requests vs. Limits and the 'Silent' OOMKill mystery.",
        "Wednesday": "AWS Cloud Architecture: Scaling Lambda for massive bursts without hitting concurrency walls.",
        "Friday": "Azure Infrastructure: Troubleshooting Transitive Routing in Hub-and-Spoke VNet peering."
    }
    
    current_topic = topic_map.get(day, "SRE & DevOps: Building resilient, cost-effective infrastructure.")

    # Modified prompt for 'Scroll-Stopping' structure and technical depth
    prompt = f"""
    Role: Senior SRE / DevOps Architect.
    Task: Write a high-quality, technical LinkedIn post titled '🚀 Tech Bytes'.
    Topic: {current_topic}.
    
    Requirements:
    1. Hook: Start with a contrarian take or a common 'production horror story' related to the topic.
    2. Deep Dive: Include one 'Did you know?' point that explains a non-obvious technical behavior (e.g., how the kernel handles cgroups or how Azure routing tables prioritize UDRs).
    3. Structure: Use short sentences and plenty of white space. No dense paragraphs.
    4. Practical Value: End with a 1-sentence tip on how to monitor or fix this issue.
    5. Hashtags: Exactly 5 hashtags, including #TechBytes #SRE #DevOps.
    
    Tone: Professional, slightly opinionated, and highly practical. Avoid corporate fluff like 'passionate' or 'leverage'.
    """

    # Using the preview model name as we discovered earlier
    response = client.models.generate_content(model="gemini-3-flash-preview", contents=prompt)
    return response.text

def post_to_linkedin(content):
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
                "shareCommentary": {"text": content},
                "shareMediaCategory": "NONE"
            }
        },
        "visibility": {"com.linkedin.ugc.MemberNetworkVisibility": "PUBLIC"}
    }
    res = requests.post(url, headers=headers, json=data)
    print(f"Status Code: {res.status_code}")

if __name__ == "__main__":
    # Check if we are in 'propose' mode or 'post' mode
    mode = sys.argv[1] if len(sys.argv) > 1 else "propose"
    
    if mode == "propose":
        print(get_gemini_content())
    elif mode == "post":
        content = os.environ.get('POST_CONTENT')
        if content:
            post_to_linkedin(content)
        else:
            print("Error: No content found to post.")
