import requests, os, hashlib, xml.etree.ElementTree as ET
from datetime import datetime, timedelta, timezone

# --- CONFIG ---
TOP_LABS = ["deepseek-ai", "openai", "anthropic"]
DISCOVERY_ORGS = ["mistralai", "meta-llama", "google-deepmind", "QwenLM", "THUDM"]
MIN_STARS = 50
INTEREST_KEYWORDS = ["reasoning", "scaling", "agent", "theorem", "video"]
PRICE_PAGES = {
    "OpenAI": "https://openai.com/api/pricing/",
    "Anthropic": "https://www.anthropic.com/pricing",
    "DeepSeek": "https://api-docs.deepseek.com/quick_start/pricing"
}

DISCORD_URL = os.getenv("DISCORD_WEBHOOK")
GITHUB_TOKEN = os.getenv("GH_TOKEN")
HF_TOKEN = os.getenv("HF_TOKEN")

def notify(msg):
    requests.post(DISCORD_URL, json={"content": msg})

def get_ai_summary(text):
    if not HF_TOKEN: return text[:300]
    try:
        url = "https://api-inference.huggingface.co/models/facebook/bart-large-cnn"
        headers = {"Authorization": f"Bearer {HF_TOKEN}"}
        response = requests.post(url, headers=headers, json={"inputs": text[:1000]})
        return "• " + response.json()[0]['summary_text'].replace(". ", "\n• ")
    except: return text[:300]

def check_github(threshold):
    headers = {"Authorization": f"token {GITHUB_TOKEN}"}
    for org in (TOP_LABS + DISCOVERY_ORGS):
        try:
            r = requests.get(f"https://api.github.com/orgs/{org}/repos?sort=created", headers=headers)
            for repo in r.json():
                created_at = datetime.strptime(repo['created_at'], "%Y-%m-%dT%H:%M:%SZ").replace(tzinfo=timezone.utc)
                if created_at > threshold:
                    if org in TOP_LABS or repo['stargazers_count'] >= MIN_STARS:
                        tag = "👑 TOP LAB" if org in TOP_LABS else "🔥 TRENDING"
                        notify(f"{tag}: **{org.upper()}**\n**Name:** {repo['name']}\n{repo['html_url']}")
        except: pass

def check_arxiv(threshold):
    query = "+OR+".join([f"all:{k}" for k in INTEREST_KEYWORDS])
    try:
        r = requests.get(f"http://export.arxiv.org/api/query?search_query={query}&sortBy=submittedDate&sortOrder=descending&max_results=10")
        root = ET.fromstring(r.content)
        for entry in root.findall('{http://www.w3.org/2005/Atom}entry'):
            pub = datetime.strptime(entry.find('{http://www.w3.org/2005/Atom}published').text, "%Y-%m-%dT%H:%M:%SZ").replace(tzinfo=timezone.utc)
            if pub > threshold:
                title = entry.find('{http://www.w3.org/2005/Atom}title').text.strip()
                link = entry.find('{http://www.w3.org/2005/Atom}id').text
                summary = get_ai_summary(entry.find('{http://www.w3.org/2005/Atom}summary').text)
                notify(f"💎 **ALPHA PAPER: {title}**\nLink: {link}\n**Summary:**\n{summary}")
    except: pass

def check_prices():
    """Detects if pricing pages have changed since the last check"""
    for lab, url in PRICE_PAGES.items():
        try:
            content = requests.get(url).text
            current_hash = hashlib.md5(content.encode()).hexdigest()
            # We use a temp file to store the 'state' between runs in GitHub Actions
            hash_file = f"{lab}_hash.txt"
            
            if os.path.exists(hash_file):
                with open(hash_file, "r") as f:
                    old_hash = f.read()
                if current_hash != old_hash:
                    notify(f"💰 **PRICE ALERT: {lab}** has updated their pricing page!\nCheck it out: {url}")
            
            with open(hash_file, "w") as f:
                f.write(current_hash)
        except: pass

if __name__ == "__main__":
    threshold = datetime.now(timezone.utc) - timedelta(minutes=65)
    check_github(threshold)
    check_arxiv(threshold)
    check_prices()
