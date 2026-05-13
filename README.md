# Frontier AI Intelligence Radar

A personal AI-ecosystem monitoring system that watches frontier-lab GitHub activity, arXiv research signals, and AI pricing-page changes, then sends concise Discord alerts.

This is not a generic monitoring dashboard. It is a lightweight **frontier AI intelligence radar**: a scheduled ops system for tracking what major AI labs and open-source model teams are shipping, researching, and pricing.

## What `watch.py` does

The core script runs three checks:

1. **GitHub frontier-lab monitoring**
   - Watches top labs: `deepseek-ai`, `openai`, `anthropic`
   - Watches discovery orgs: `mistralai`, `meta-llama`, `google-deepmind`, `QwenLM`, `THUDM`
   - Flags newly created repositories inside the recent execution window
   - Always alerts for top-lab repos
   - Alerts for discovery-org repos when they cross the configured star threshold

2. **arXiv research monitoring**
   - Searches arXiv for current papers matching interest keywords:
     - `reasoning`
     - `scaling`
     - `agent`
     - `theorem`
     - `video`
   - Pulls the latest submitted papers
   - Uses Hugging Face Inference Router summarization when an HF token is available
   - Sends short paper summaries to Discord

3. **AI pricing-page change detection**
   - Watches pricing pages for:
     - OpenAI
     - Anthropic
     - DeepSeek
   - Hashes page content
   - Compares current hash against the previous run
   - Sends Discord alert when a pricing page changes

## Operating model

```text
GitHub Actions cron / manual run
        |
        v
watch.py
        |
        |-- GitHub org scan
        |-- arXiv keyword scan
        |-- pricing-page hash check
        |
        v
Delta detection / filtering
        |
        |-- new repos
        |-- recent papers
        |-- pricing hash changes
        |
        v
Optional AI summarization
        |
        v
Discord webhook alert
```

The system is designed to run on a schedule, usually through GitHub Actions. Hash files are used as lightweight state so the system can detect changes between runs.

## Why this matters

The AI ecosystem changes too fast for manual tracking:

- frontier labs quietly create repositories before public announcements
- open-source model teams release tooling and examples before media coverage catches up
- arXiv papers reveal research direction before productization
- pricing-page changes signal commercial strategy shifts
- Discord alerts turn passive browsing into an active intelligence feed

Most candidates show toy chatbots. This project shows a personal operating system for tracking the frontier AI landscape with automation, summarization, and alerting.

## Tech stack

- Python
- GitHub REST API
- arXiv Atom API
- Hugging Face Inference Router
- Discord Webhooks
- `requests`
- `xml.etree.ElementTree`
- `hashlib`
- GitHub Actions scheduled execution
- file-based state / repo-cache style delta detection

## Configuration

The script expects these environment variables:

```bash
DISCORD_WEBHOOK=your_discord_webhook_url
GH_TOKEN=your_github_token
HF_TOKEN=your_huggingface_token_optional
```

`HF_TOKEN` is optional. If unavailable, the script falls back to truncated abstracts instead of AI summaries.

## Main configuration in code

```python
TOP_LABS = ["deepseek-ai", "openai", "anthropic"]
DISCOVERY_ORGS = ["mistralai", "meta-llama", "google-deepmind", "QwenLM", "THUDM"]
MIN_STARS = 50
INTEREST_KEYWORDS = ["reasoning", "scaling", "agent", "theorem", "video"]
PRICE_PAGES = {
    "OpenAI": "https://openai.com/api/pricing/",
    "Anthropic": "https://www.anthropic.com/pricing",
    "DeepSeek": "https://api-docs.deepseek.com/quick_start/pricing"
}
```

## Example alerts

```text
👑 TOP LAB: OPENAI
Name: example-repo
https://github.com/openai/example-repo
```

```text
💎 ALPHA PAPER: New Reasoning Model Paper
Link: https://arxiv.org/abs/...
Summary:
• Short AI-generated summary bullet
• Key finding
• Why it matters
```

```text
💰 PRICE ALERT: Anthropic has updated their pricing page!
Check it out: https://www.anthropic.com/pricing
```

## Production hardening roadmap

The current implementation is intentionally lightweight. To harden it further:

- add a GitHub Actions workflow file with hourly cron and manual dispatch
- store hash/state files using GitHub Actions cache or committed state artifacts
- add retry/backoff for GitHub, arXiv, Hugging Face, and pricing-page requests
- add structured JSON logs
- add duplicate suppression across multiple alert types
- add severity scoring for repos/papers/pricing changes
- add Slack/Telegram/email notification adapters
- add RSS output
- add SQLite/Postgres persistence for long-term trend analysis
- add dashboard for historical lab/research/pricing changes
- add keyword groups by theme: agents, inference, evals, video, theorem proving, robotics, pricing
- add tests for XML parsing, hash comparison, summarization fallback, and webhook formatting

## Resume positioning

This project supports the following claims:

- AI ecosystem intelligence automation
- frontier-lab monitoring
- GitHub API automation
- arXiv research tracking
- scheduled ops via GitHub Actions
- AI summarization using Hugging Face inference
- stateful delta detection
- Discord/webhook alerting
- practical automation beyond generic chatbot demos

## Repository status

Working personal intelligence radar built around `watch.py`. The project is intentionally small, but the idea is unusual and practical: monitor frontier AI movement continuously instead of manually browsing announcements after everyone else has seen them.
