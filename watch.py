import requests
import json
import os
import time

# --- CONFIGURATION ---
ORGS = [
    "deepseek-ai", "black-forest-labs", "xai-org", "ByteDance-Seed", 
    "anthropics", "openai", "mistralai", "meta-llama", "google-deepmind", 
    "lucidrains", "togethercomputer", "microsoft", "QwenLM"
]
# It will try to find these from your system/GitHub Actions environment
DISCORD_WEBHOOK_URL = os.getenv("DISCORD_WEBHOOK_URL", "https://discord.com/api/webhooks/1464238545660285021/qZlm8arNPo0y_aRKxVvVz-zGKJx5Z9JwWMfpxAgds2ehb-yiJlS2ZLR3gUrDNDM-hYAW")
GITHUB_TOKEN = os.getenv("GITHUB_TOKEN", "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")
STATE_FILE = "seen_repos.json"

def notify(message):
    print(f"[!] {message}")
    if "PASTE_YOUR_WEBHOOK" not in DISCORD_WEBHOOK_URL:
        requests.post(DISCORD_WEBHOOK_URL, json={"content": message})

def get_seen_repos():
    if os.path.exists(STATE_FILE):
        try:
            with open(STATE_FILE, "r") as f:
                return set(json.load(f))
        except: return set()
    return set()

def save_seen_repos(seen):
    with open(STATE_FILE, "w") as f:
        json.dump(list(seen), f)

def check_new_repos():
    seen = get_seen_repos()
    headers = {"Authorization": f"token {GITHUB_TOKEN}"}
    new_finds = False

    for org in ORGS:
        url = f"https://api.github.com/orgs/{org}/repos?sort=created&direction=desc"
        try:
            response = requests.get(url, headers=headers)
            repos = response.json()
            
            # SAFETY CHECK: If GitHub sends an error instead of a list, skip it
            if not isinstance(repos, list):
                print(f"[-] GitHub API error for {org}: {repos.get('message', 'Unknown Error')}")
                continue

            for repo in repos:
                repo_id = str(repo['id'])
                if repo_id not in seen:
                    # Filter out boring updates - only notify for truly new/interesting names
                    msg = f"🚀 **NEW DROP: {org.upper()}**\n**Name:** {repo['name']}\n**Link:** {repo['html_url']}\n**Description:** {repo['description']}"
                    notify(msg)
                    seen.add(repo_id)
                    new_finds = True
        except Exception as e:
            print(f"Error checking {org}: {e}")

    if new_finds:
        save_seen_repos(seen)

if __name__ == "__main__":
    print("Radar Active. I will only ping for NEW repositories now.")
    check_new_repos() # Run once at start
