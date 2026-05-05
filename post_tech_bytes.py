import os
import requests
import datetime
import sys
from google import genai

# Load secrets
L_TOKEN = os.environ.get('LINKEDIN_TOKEN')
L_AUTH_ID = os.environ.get('LINKEDIN_AUTHOR_ID')
GEM_KEY = os.environ.get('GEMINI_API_KEY')

def get_gemini_content():
    client = genai.Client(api_key=GEM_KEY)
    now = datetime.datetime.now()
    day_name = now.strftime("%A")
    day_of_year = now.timetuple().tm_yday
    idx = day_of_year % 5 # Rotates through sub-topics

    # Define Topic Lists
    topics = {
        "Monday": ["Gateway API vs Ingress", "etcd consistency tuning", "CRD Finalizers", "Sidecar Lifecycle", "K8s Network Policies"],
        "Tuesday": ["EKS Pod Identity", "Lambda SnapStart", "VPC Lattice", "IAM Permissions Boundary", "Graviton Migration"],
        "Wednesday": ["AKS Fleet Manager", "Entra ID Workload Identity", "App Service Sidecars", "Spot Node Eviction", "Azure CNI eBPF"],
        "Thursday": ["Terraform State Locking", "Terragrunt DRY modules", "Terraform Drift Detection", "Provider Versioning", "OIDC for Terraform Cloud"],
        "Friday": ["Prometheus Cardinality", "eBPF Tracing", "OpenTelemetry 2.0", "Loki Log Aggregation", "Golden Signals Monitoring"]
    }

    if day_name == "Saturday":
        prompt = f"""
        Context: You are a Senior SRE Interviewer.
        Task: Provide 3 high-quality DevOps/SRE Interview Questions for your 'Tech Bytes' series.
        Format: 
        1. A Scenario-based question.
        2. A Deep-dive technical question (Networking/Linux).
        3. A 'Cultural/SRE' philosophy question.
        Include brief 'Pro-tips' for the answers.
        Timestamp: 🕒 Interview Prep | {now.strftime('%Y-%m-%d')}
        Hashtags: #TechBytes #SRE #DevOps #InterviewPrep #CareerGrowth
        """
    else:
        current_topic = topics.get(day_name, ["General DevOps Architecture"])[idx]
        prompt = f"""
        Context: Senior SRE (6 years exp). 
        Topic: {day_name} Focus - {current_topic}.
        Task: Write a 'Problem-Solution' LinkedIn post titled '🚀 Tech Bytes'.
        Requirements: High technical depth, 2026 best practices, and a catchy hook.
        Timestamp: 🕒 2026 Insights | {now.strftime('%Y-%m-%d')}
        Hashtags: #TechBytes #SRE #DevOps #CloudNative #{day_name}
        """

    response = client.models.generate_content(model="gemini-3-flash-preview", contents=prompt)
    return response.text.strip()

def post_to_linkedin(content):
    content_to_post = os.environ.get('POST_CONTENT', content)
    url = "https://api.linkedin.com/v2/ugcPosts"
    headers = {"Authorization": f"Bearer {L_TOKEN}", "Content-Type": "application/json", "X-Restli-Protocol-Version": "2.0.0"}
    data = {
        "author": L_AUTH_ID, "lifecycleState": "PUBLISHED",
        "specificContent": {"com.linkedin.ugc.ShareContent": {"shareCommentary": {"text": content_to_post}, "shareMediaCategory": "NONE"}},
        "visibility": {"com.linkedin.ugc.MemberNetworkVisibility": "PUBLIC"}
    }
    return requests.post(url, headers=headers, json=data)

if __name__ == "__main__":
    mode = sys.argv[1] if len(sys.argv) > 1 else "propose"
    if mode == "propose":
        print(get_gemini_content())
    elif mode == "post":
        res = post_to_linkedin("")
        print(f"Status: {res.status_code}")
