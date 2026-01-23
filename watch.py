import requests
import json
import os
import time

# --- PASTE YOUR DATA HERE ---
ORGS = ["deepseek-ai", "openai", "anthropics", "mistralai", "meta-llama"]
DISCORD_WEBHOOK_URL = "https://discord.com/api/webhooks/1464238545660285021/qZlm8arNPo0y_aRKxVvVz-zGKJx5Z9JwWMfpxAgds2ehb-yiJlS2ZLR3gUrDNDM-hYAW" 
GITHUB_TOKEN = "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"
# ----------------------------

STATE_FILE = "seen_repos.json"

def notify(message):
    print(f"[!] {message}")
    requests.post(DISCORD_WEBHOOK_URL, json={"content": message})

def get_seen_repos():
    if os.path.exists(STATE_FILE):
        with open(STATE_FILE, "r") as f:
            return set(json.load(f))
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
            for repo in repos:
                repo_id = str(repo['id'])
                if repo_id not in seen:
                    msg = f"🚨 **NEW REPO DETECTED: {org.upper()}**\n**Name:** {repo['name']}\n**Link:** {repo['html_url']}\n**Description:** {repo['description']}"
                    notify(msg)
                    seen.add(repo_id)
                    new_finds = True
        except Exception as e:
            print(f"Error checking {org}: {e}")

    if new_finds:
        save_seen_repos(seen)

if __name__ == "__main__":
    print("Radar is active. Checking every 5 minutes...")
    while True:
        check_new_repos()
        time.sleep(300)