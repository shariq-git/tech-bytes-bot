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
    
    # 1. Logic for 30-day variety
    now = datetime.datetime.now()
    day_name = now.strftime("%A")
    day_of_year = now.timetuple().tm_yday
    
    # Advanced 2026 sub-topics for rotation
    k8s_sub = ["Gateway API vs Ingress", "eBPF Observability", "etcd consistency tuning", "Custom Resource Definitions (CRDs)", "Sidecar containers in K8s 1.29+"]
    aws_sub = ["EKS Pod Identity", "Lambda SnapStart latency", "VPC Lattice networking", "IAM Permissions Boundary", "Cost-effective Graviton migration"]
    azure_sub = ["AKS Fleet Manager", "Azure CNI Powered by eBPF", "App Service Sidecars", "Workload Identity Federation", "Spot Node eviction handling"]

    # 2. Assign dynamic topic based on day and rotation index
    index = day_of_year % 5
    if day_name == "Monday":
        current_topic = f"Kubernetes: {k8s_sub[index]}"
    elif day_name == "Wednesday":
        current_topic = f"AWS Cloud: {aws_sub[index]}"
    elif day_name == "Friday":
        current_topic = f"Azure Infra: {azure_sub[index]}"
    else:
        current_topic = "Advanced SRE Automation & Platform Engineering"

    # 3. Enhanced "Problem-Solution" Prompt
    prompt = f"""
    Context: You are a Senior DevOps/SRE with 6 years of experience. Today's date is {now.strftime('%Y-%m-%d')}.
    Target Audience: Technical engineers, architects, and SREs.
    
    Task: Write a LinkedIn post titled '🚀 Tech Bytes' focusing on: {current_topic}.
    
    Requirements:
    - Use a 'Problem-Solution' framework: Briefly describe a real-world engineering hurdle and how to solve it using latest 2026 best practices.
    - Content must be technical: Mention specific tools, configurations, or architectural patterns.
    - Style: Professional, concise, and insightful (not a tutorial).
    - Add a timestamp: '🕒 2026 Insights | [Current Time] IST'.
    - Use exactly 5 hashtags: #TechBytes #SRE #DevOps #CloudNative and the relevant platform tag (#Kubernetes, #AWS, or #Azure).
    """
    
    response = client.models.generate_content(model="gemini-3-flash-preview", contents=prompt)
    return response.text.strip()

def post_to_linkedin(content):
    # Retrieve content from environment variable if passed by GitHub Action
    # or use the content passed directly to the function
    content_to_post = os.environ.get('POST_CONTENT', content)
    
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
    return requests.post(url, headers=headers, json=data)

if __name__ == "__main__":
    # Support for the two-stage GitHub Action workflow
    mode = sys.argv[1] if len(sys.argv) > 1 else "propose"
    
    if mode == "propose":
        # Just generate and print for the approval gate logs
        print(get_gemini_content())
    elif mode == "post":
        # Actually execute the post
        res = post_to_linkedin("") 
        print(f"LinkedIn Status Code: {res.status_code}")
