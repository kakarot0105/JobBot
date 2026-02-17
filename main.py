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
NOTIFICATION_CHAT_ID = -5237585056  # JobBot Alerts group
TELEGRAM_TOKEN = os.getenv("TELEGRAM_TOKEN", "")

DEFAULT_FILTERS = {
    "keywords": ["Data Engineer"],
    "location": "USA,Remote",
    "salary_min": None,
    "level": "Mid",
    "job_type": ["Contract", "Full-time"]
}


async def setup_user():
    """Setup default user with preferences."""
    user_id = add_user(DEFAULT_USER_TELEGRAM_ID, "banna")
    set_filters(
        user_id,
        keywords=DEFAULT_FILTERS["keywords"],
        location=DEFAULT_FILTERS["location"],
        salary_min=DEFAULT_FILTERS.get("salary_min"),
        level=DEFAULT_FILTERS.get("level"),
        job_type=DEFAULT_FILTERS.get("job_type")
    )
    print(f"✅ User setup complete: {user_id}")
    return user_id


async def daily_search(use_mock: bool = False, send_telegram: bool = True):
    """Run daily job search."""
    print("\n🔍 Starting daily job search...")
    user_id = await setup_user()
    
    try:
        # Try real search first
        jobs = await search_jobs_for_user(user_id)
        
        # If no jobs found and in test mode, use mock data
        if not jobs and use_mock:
            print("⚠️  External APIs unavailable (sandbox environment)")
            print("📌 Using mock job data for demonstration...")
            jobs = get_mock_jobs()
        
        print(f"✅ Found {len(jobs)} jobs!")
        
        # Send to Telegram if token is available
        if send_telegram and TELEGRAM_TOKEN and jobs:
            try:
                bot = Bot(token=TELEGRAM_TOKEN)
                for job in jobs[:10]:  # Send top 10
                    msg = f"""
💼 **{job['title']}**
🏢 {job['company']}
📍 {job['location']}
💰 {job['salary']}
⏰ {job['job_type']}

[Apply Here]({job['url']})
"""
                    await bot.send_message(
                        chat_id=NOTIFICATION_CHAT_ID,
                        text=msg,
                        parse_mode="Markdown"
                    )
                    await asyncio.sleep(0.5)
                print(f"📨 Sent {min(10, len(jobs))} jobs to Telegram!")
            except Exception as e:
                print(f"⚠️  Could not send Telegram: {e}")
        
        # Print first 10 jobs
        for i, job in enumerate(jobs[:10]):
            print(f"\n{i+1}. {job['title']} @ {job['company']}")
            print(f"   Location: {job['location']}")
            print(f"   Salary: {job['salary']}")
            print(f"   Type: {job['job_type']}")
            print(f"   Source: {job['source']}")
            print(f"   URL: {job['url']}")
    except Exception as e:
        print(f"❌ Error: {e}")


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
