import requests
import os
import xml.etree.ElementTree as ET
from datetime import datetime, timedelta, timezone

# --- CONFIGURATION ---
ORGS = ["deepseek-ai", "black-forest-labs", "xai-org", "anthropics", "openai", "mistralai", "meta-llama", "google-deepmind", "QwenLM", "THUDM"]
# Keywords to stalk on ArXiv
RESEARCH_LABS = ["DeepSeek", "OpenAI", "Anthropic", "Mistral AI", "Google DeepMind", "Meta AI"]

DISCORD_URL = os.getenv("DISCORD_WEBHOOK")
GITHUB_TOKEN = os.getenv("GH_TOKEN")

def notify(msg):
    print(f"[!] Sending: {msg}")
    requests.post(DISCORD_URL, json={"content": msg})

def check_github(threshold):
    headers = {"Authorization": f"token {GITHUB_TOKEN}"}
    for org in ORGS:
        url = f"https://api.github.com/orgs/{org}/repos?sort=created&direction=desc"
        try:
            r = requests.get(url, headers=headers)
            repos = r.json()
            if not isinstance(repos, list): continue
            for repo in repos:
                created_at = datetime.strptime(repo['created_at'], "%Y-%m-%dT%H:%M:%SZ").replace(tzinfo=timezone.utc)
                if created_at > threshold:
                    notify(f"🚀 **NEW REPO: {org.upper()}**\n**Name:** {repo['name']}\n{repo['html_url']}")
        except Exception as e: print(f"GH Error {org}: {e}")

def check_arxiv(threshold):
    for lab in RESEARCH_LABS:
        # Search ArXiv for the lab name in all fields, sorted by last updated
        url = f"http://export.arxiv.org/api/query?search_query=all:{lab.replace(' ', '+')}&sortBy=submittedDate&sortOrder=descending&max_results=5"
        try:
            r = requests.get(url)
            root = ET.fromstring(r.content)
            # ArXiv uses Atom feed format
            for entry in root.findall('{http://www.w3.org/2005/Atom}entry'):
                published_str = entry.find('{http://www.w3.org/2005/Atom}published').text
                published = datetime.strptime(published_str, "%Y-%m-%dT%H:%M:%SZ").replace(tzinfo=timezone.utc)
                
                if published > threshold:
                    title = entry.find('{http://www.w3.org/2005/Atom}title').text.strip()
                    link = entry.find('{http://www.w3.org/2005/Atom}id').text
                    notify(f"📄 **NEW PAPER: {lab}**\n**Title:** {title}\n**Link:** {link}")
        except Exception as e: print(f"ArXiv Error {lab}: {e}")

if __name__ == "__main__":
    # Check for anything in the last 1 hour (plus 5 min buffer)
    time_threshold = datetime.now(timezone.utc) - timedelta(days=1)
    print(f"Scanning since {time_threshold}")
    
    check_github(time_threshold)
    check_arxiv(time_threshold)
    print("Scan complete.")

