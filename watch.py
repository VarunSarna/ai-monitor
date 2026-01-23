import requests
import os
import xml.etree.ElementTree as ET
from datetime import datetime, timedelta, timezone

# --- CONFIG ---
TOP_LABS = ["deepseek-ai", "openai", "anthropic"]
DISCOVERY_ORGS = ["mistralai", "meta-llama", "google-deepmind", "QwenLM", "THUDM", "black-forest-labs"]
MIN_STARS = 50
INTEREST_KEYWORDS = ["reasoning", "scaling", "agent", "theorem", "discovery", "video"]

DISCORD_URL = os.getenv("DISCORD_WEBHOOK")
GITHUB_TOKEN = os.getenv("GH_TOKEN")

def notify(msg):
    print(f"Sending: {msg}")
    requests.post(DISCORD_URL, json={"content": msg})

def check_github(threshold):
    headers = {"Authorization": f"token {GITHUB_TOKEN}"}
    for org in (TOP_LABS + DISCOVERY_ORGS):
        url = f"https://api.github.com/orgs/{org}/repos?sort=updated"
        try:
            r = requests.get(url, headers=headers)
            repos = r.json()
            for repo in repos:
                # Use 'created_at' to find brand new drops
                created_at = datetime.strptime(repo['created_at'], "%Y-%m-%dT%H:%M:%SZ").replace(tzinfo=timezone.utc)
                if created_at > threshold:
                    if org in TOP_LABS or repo['stargazers_count'] >= MIN_STARS:
                        tag = "👑 TOP LAB" if org in TOP_LABS else "🔥 TRENDING"
                        notify(f"{tag}: **{org.upper()}**\n**Name:** {repo['name']}\n{repo['html_url']}")
        except: pass

def check_arxiv(threshold):
    search_query = "+OR+".join([f"all:{k}" for k in INTEREST_KEYWORDS])
    url = f"http://export.arxiv.org/api/query?search_query={search_query}&sortBy=submittedDate&sortOrder=descending&max_results=10"
    try:
        r = requests.get(url)
        root = ET.fromstring(r.content)
        for entry in root.findall('{http://www.w3.org/2005/Atom}entry'):
            pub_str = entry.find('{http://www.w3.org/2005/Atom}published').text
            pub = datetime.strptime(pub_str, "%Y-%m-%dT%H:%M:%SZ").replace(tzinfo=timezone.utc)
            if pub > threshold:
                title = entry.find('{http://www.w3.org/2005/Atom}title').text.strip()
                link = entry.find('{http://www.w3.org/2005/Atom}id').text
                notify(f"💎 **ALPHA PAPER FOUND**\n**Title:** {title}\n**Link:** {link}")
    except: pass

if __name__ == "__main__":
    # 65 minutes ensures we don't miss anything between hourly GitHub Action runs
    time_threshold = datetime.now(timezone.utc) - timedelta(minutes=65)
    check_github(time_threshold)
    check_arxiv(time_threshold)
