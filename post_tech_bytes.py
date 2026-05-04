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
    
    # Get current day of the week
    day = datetime.datetime.now().strftime("%A")
    
    # Assign topic based on your specific schedule
    topic_map = {
        "Monday": "Kubernetes internals (e.g., ETCD, Control Plane, or CRDs)",
        "Wednesday": "AWS Cloud Architecture (e.g., EKS, IAM, or Lambda scaling)",
        "Friday": "Azure Infrastructure (e.g., Azure Kubernetes Service (AKS), App Services, or VNet peering)"
    }
    
    # Default topic if the day doesn't match (for manual runs)
    current_topic = topic_map.get(day, "DevOps and SRE best practices")

    prompt = f"""
    Write a high-quality, technical LinkedIn post titled '🚀 Tech Bytes'.
    Specific Topic for today: {current_topic}.
    
    Requirements:
    - Start with a catchy hook for a technical audience.
    - Include one "Deep Dive" fact or advanced technical tip about {current_topic}.
    - Mention why this is critical for modern SRE/DevOps workflows.
    - Add a timestamp: '🕒 Posted at [Current Time] IST'.
    - Use exactly 5 hashtags including #TechBytes #SRE #DevOps and the specific platform (e.g., #Kubernetes, #AWS, or #Azure).
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
