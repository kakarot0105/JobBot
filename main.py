#!/usr/bin/env python3
"""JobBot - Automated job search and notifications."""
import asyncio
import os
import sys
from app.db import add_user, set_filters
from app.jobs import search_jobs_for_user
from app.telegram_bot import create_bot
from app.mock_jobs import get_mock_jobs
from telegram import Bot

# Hardcoded user preferences (for @banna)
DEFAULT_USER_TELEGRAM_ID = "6756402815"
TELEGRAM_TOKEN = os.getenv("TELEGRAM_TOKEN", "")

# Multiple job profiles — each with its own Telegram group
JOB_PROFILES = [
    {
        "name": "Data Engineer",
        "chat_id": -1003357441031,
        "filters": {
            "keywords": ["Data Engineer"],
            "location": "USA,Remote",
            "salary_min": None,
            "level": "Mid",
            "job_type": ["Contract", "Full-time"],
        },
    },
    {
        "name": "QA Engineer",
        "chat_id": -5015437084,
        "filters": {
            "keywords": ["QA Engineer"],
            "location": "USA,Remote",
            "salary_min": None,
            "level": "Mid",
            "job_type": ["Contract", "Full-time"],
        },
    },
]


async def setup_user_for_profile(profile: dict) -> int:
    """Setup user with filters for a specific job profile."""
    user_id = add_user(DEFAULT_USER_TELEGRAM_ID, "banna")
    f = profile["filters"]
    set_filters(
        user_id,
        keywords=f["keywords"],
        location=f["location"],
        salary_min=f.get("salary_min"),
        level=f.get("level"),
        job_type=f.get("job_type"),
    )
    return user_id


async def send_jobs_to_telegram(jobs: list, chat_id: int, profile_name: str):
    """Send job list to a specific Telegram chat."""
    if not TELEGRAM_TOKEN or not jobs:
        return
    try:
        bot = Bot(token=TELEGRAM_TOKEN)
        for job in jobs[:10]:
            msg = f"""
💼 **{job['title']}**
🏢 {job['company']}
📍 {job['location']}
💰 {job['salary']}
⏰ {job['job_type']}

[Apply Here]({job['url']})
"""
            await bot.send_message(chat_id=chat_id, text=msg, parse_mode="Markdown")
            await asyncio.sleep(0.5)
        print(f"  📨 Sent {min(10, len(jobs))} jobs to [{profile_name}] group!")
    except Exception as e:
        print(f"  ⚠️  Telegram error for [{profile_name}]: {e}")


async def daily_search(use_mock: bool = False, send_telegram: bool = True):
    """Run daily job search across all profiles."""
    print("\n🔍 Starting daily job search...")

    for profile in JOB_PROFILES:
        name = profile["name"]
        chat_id = profile["chat_id"]
        print(f"\n── {name} ──")

        user_id = await setup_user_for_profile(profile)

        try:
            jobs = await search_jobs_for_user(user_id)

            if not jobs and use_mock:
                print("  ⚠️  External APIs unavailable — using mock data")
                jobs = get_mock_jobs()

            print(f"  ✅ Found {len(jobs)} jobs")

            if send_telegram:
                await send_jobs_to_telegram(jobs, chat_id, name)

            for i, job in enumerate(jobs[:10]):
                print(f"  {i+1}. {job['title']} @ {job['company']}")
                print(f"     📍 {job['location']} | 💰 {job['salary']} | {job['source']}")
        except Exception as e:
            print(f"  ❌ Error: {e}")


async def main():
    """Main entry point."""
    if len(sys.argv) > 1:
        if sys.argv[1] == "search":
            # Run job search (production - send to Telegram)
            use_mock = "--mock" in sys.argv
            await daily_search(use_mock=use_mock, send_telegram=True)
        elif sys.argv[1] == "test":
            # Run with mock data for testing (no Telegram)
            await daily_search(use_mock=True, send_telegram=False)
        elif sys.argv[1] == "telegram":
            # Run Telegram bot
            print("🤖 Starting Telegram bot...")
            app = create_bot()
            await app.run_polling()
        elif sys.argv[1] == "setup":
            # Setup user
            await setup_user()
        else:
            print("Usage:")
            print("  python main.py search        - Run job search (sends to Telegram)")
            print("  python main.py test          - Run with mock jobs (no Telegram)")
            print("  python main.py search --mock - Force mock data")
            print("  python main.py telegram      - Start Telegram bot")
            print("  python main.py setup         - Setup default user")
    else:
        # Default: run both
        print("JobBot - Automated Job Search")
        print("=" * 40)
        
        # Setup user
        await setup_user()
        
        # Search jobs (with mock fallback, send to Telegram)
        await daily_search(use_mock=True, send_telegram=True)
        
        print("\n" + "=" * 40)
        print("To use Telegram bot, run: python main.py telegram")


if __name__ == "__main__":
    asyncio.run(main())
