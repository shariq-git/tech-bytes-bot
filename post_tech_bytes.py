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
    topic_map = {
        "Monday": "Kubernetes trends and working ",
        "Wednesday": "AWS Cloud Architecture (e.g., EKS, IAM, or Lambda scaling)",
        "Friday": "Azure Infrastructure (e.g., AKS, App Services, or VNet peering)"
    }
    current_topic = topic_map.get(day, "DevOps and SRE best practices")

    prompt = f"""
    Write a high-quality, technical LinkedIn post titled '🚀 Tech Bytes'.
    Topic: {current_topic}.
    Requirements:
    - Start with a catchy hook.
    - Include one deep-dive technical 'Did you know?' point.
    - Use exactly 5 hashtags including #TechBytes #SRE #DevOps.
    - Keep it professional and insightful.
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
