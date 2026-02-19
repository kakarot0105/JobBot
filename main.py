#!/usr/bin/env python3
"""JobBot - Automated job search and notifications."""
import asyncio
import os
import sys
from app.db import add_user, set_filters, add_job, is_job_sent, mark_sent
from app.jobs import JobScraper
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
            "keywords": ["AWS Data Engineer", "Data Engineer", "Cloud Engineer", "AI Data Engineer", "Azure Data Engineer"],
            "location": "USA",
            "salary_min": 100000,
            "level": "Mid,Senior",
            "job_type": ["Full-time"],
        },
    },
    {
        "name": "Quality Engineer",
        "chat_id": -5015437084,
        "filters": {
            "keywords": ["Quality Engineer", "CAPA", "Process Improvement", "Supply Quality", "Manufacturing Quality", "FMEA", "DMAIC", "Compliance"],
            "location": "USA",
            "salary_min": 85000,
            "level": "Mid,Senior",
            "job_type": ["Full-time"],
        },
    },
]


scraper = JobScraper()


async def send_jobs_to_telegram(jobs: list, chat_id: int, profile_name: str, user_id: int):
    """Send only NEW jobs to a specific Telegram chat."""
    if not TELEGRAM_TOKEN or not jobs:
        return 0
    sent = 0
    try:
        bot = Bot(token=TELEGRAM_TOKEN)
        for job in jobs:
            # Skip already-sent jobs
            if is_job_sent(job['url'], chat_id):
                continue
            msg = f"""
💼 **{job['title']}**
🏢 {job['company']}
📍 {job['location']}
💰 {job['salary']}
⏰ {job['job_type']}

[Apply Here]({job['url']})
"""
            await bot.send_message(chat_id=chat_id, text=msg, parse_mode="Markdown")
            # Store in DB and mark as sent
            job_id = add_job(
                title=job['title'], company=job['company'], location=job['location'],
                salary=job['salary'], job_type=job['job_type'], source=job['source'],
                url=job['url'], description=job.get('description')
            )
            mark_sent(user_id, job_id, chat_id)
            sent += 1
            await asyncio.sleep(0.5)
            if sent >= 10:
                break
        if sent:
            print(f"  📨 Sent {sent} NEW jobs to [{profile_name}]!")
        else:
            print(f"  ✅ No new jobs for [{profile_name}] (all already sent)")
    except Exception as e:
        print(f"  ⚠️  Telegram error for [{profile_name}]: {e}")
    return sent


async def daily_search(use_mock: bool = False, send_telegram: bool = True):
    """Run daily job search across all profiles."""
    print("\n🔍 Starting daily job search...")

    user_id = add_user(DEFAULT_USER_TELEGRAM_ID, "banna")

    for profile in JOB_PROFILES:
        name = profile["name"]
        chat_id = profile["chat_id"]
        print(f"\n── {name} ──")

        f = profile["filters"]
        try:
            jobs = await scraper.search_all(
                keywords=f["keywords"],
                location=f["location"],
                salary_min=f.get("salary_min"),
                level=f.get("level"),
                job_type=f.get("job_type"),
            )

            if not jobs and use_mock:
                print("  ⚠️  External APIs unavailable — using mock data")
                jobs = get_mock_jobs()

            print(f"  ✅ Found {len(jobs)} jobs")

            if send_telegram:
                await send_jobs_to_telegram(jobs, chat_id, name, user_id)

            for i, job in enumerate(jobs[:10]):
                print(f"  {i+1}. {job['title']} @ {job['company']}")
                print(f"     📍 {job['location']} | 💰 {job['salary']} | {job['source']}")
        except Exception as e:
            print(f"  ❌ Error: {e}")


async def main():
    """Main entry point."""
    run_mode = os.getenv("RUN_MODE", "").lower()
    if run_mode == "search":
        use_mock = os.getenv("RUN_MOCK", "false").lower() == "true"
        await daily_search(use_mock=use_mock, send_telegram=True)
        return

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
