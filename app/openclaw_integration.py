"""OpenClaw integration for JobBot notifications."""
import json
import os
from pathlib import Path


def get_openclaw_token() -> str:
    """Get Telegram bot token from OpenClaw config."""
    config_path = Path.home() / ".openclaw" / "openclaw.json"
    
    if not config_path.exists():
        raise FileNotFoundError("OpenClaw config not found at ~/.openclaw/openclaw.json")
    
    with open(config_path) as f:
        config = json.load(f)
    
    token = config.get("channels", {}).get("telegram", {}).get("botToken")
    if not token or token == "__OPENCLAW_REDACTED__":
        raise ValueError("Telegram token not available or redacted in config")
    
    return token


def format_job_message(jobs: list) -> str:
    """Format jobs for Telegram."""
    if not jobs:
        return "😕 No new Data Engineer jobs found today."
    
    msg = f"🔍 **Found {len(jobs)} Data Engineer Jobs**\n\n"
    
    for i, job in enumerate(jobs[:10], 1):  # Max 10 jobs per message
        msg += f"{i}. **{job['title']}** @ {job['company']}\n"
        msg += f"   📍 {job['location']} | {job['job_type']}\n"
        msg += f"   💰 {job['salary']}\n"
        msg += f"   🔗 [Apply]({job['url']})\n\n"
    
    if len(jobs) > 10:
        msg += f"\n... and {len(jobs) - 10} more jobs available!"
    
    return msg
