import os
import requests
import datetime
from google import genai

# Load secrets from GitHub
L_TOKEN = os.environ['LINKEDIN_TOKEN']
L_AUTH_ID = os.environ['LINKEDIN_AUTHOR_ID']
GEM_KEY = os.environ['GEMINI_API_KEY']

def get_gemini_content():
    client = genai.Client(api_key=GEM_KEY)
    
    # Advanced SRE/DevOps topics
    prompt = """
    Write a high-quality, technical LinkedIn post titled '🚀 Tech Bytes'.
    Topic: Advanced DevOps/SRE (e.g., K8s internals, Docker security,AWS ,Azure or Cloud Architecture).
    Requirements:
    - Start with a catchy hook.
    - Include one deep-dive technical 'Did you know?' point.
    - Add a timestamp: '🕒 Posted at [Current Time] IST'.
    - Use exactly 5 hashtags including #TechBytes #SRE #DevOps.
    - Keep it professional and insightful.
    """
    
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
    return requests.post(url, headers=headers, json=data)

if __name__ == "__main__":
    content = get_gemini_content()
    res = post_to_linkedin(content)
    print(f"Status Code: {res.status_code}")
    print(f"Response: {res.text}")
