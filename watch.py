import requests
import os
from datetime import datetime, timedelta, timezone

# The "Alpha" List
ORGS = [
    "deepseek-ai", "black-forest-labs", "xai-org", "ByteDance-Seed", 
    "anthropics", "openai", "mistralai", "meta-llama", "google-deepmind", 
    "lucidrains", "togethercomputer", "microsoft", "QwenLM", "THUDM"
]

DISCORD_URL = os.getenv("DISCORD_WEBHOOK")
GITHUB_TOKEN = os.getenv("GH_TOKEN")

def notify(msg):
    requests.post(DISCORD_URL, json={"content": msg})

def check():
    headers = {"Authorization": f"token {GITHUB_TOKEN}"}
    # Look for anything created in the last 65 minutes
    now = datetime.now(timezone.utc)
    threshold = now - timedelta(minutes=65)

    for org in ORGS:
        url = f"https://api.github.com/orgs/{org}/repos?sort=created&direction=desc"
        try:
            r = requests.get(url, headers=headers)
            repos = r.json()
            if not isinstance(repos, list): continue

            for repo in repos:
                # Convert GitHub time string to actual time object
                created_at = datetime.strptime(repo['created_at'], "%Y-%m-%dT%H:%M:%SZ").replace(tzinfo=timezone.utc)
                
                if created_at > threshold:
                    msg = f"🚨 **NEW DROP: {org.upper()}**\n**Repo:** {repo['name']}\n{repo['html_url']}"
                    notify(msg)
        except Exception as e:
            print(f"Error checking {org}: {e}")

if __name__ == "__main__":
    check()
