#!/usr/bin/env python3
"""JobBot - Automated job search and notifications."""
import asyncio
import os
from app.db import add_user, set_filters
from app.jobs import search_jobs_for_user
from app.telegram_bot import create_bot

# Hardcoded user preferences (for @banna)
DEFAULT_USER_TELEGRAM_ID = "6756402815"
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


async def daily_search():
    """Run daily job search."""
    print("\n🔍 Starting daily job search...")
    user_id = await setup_user()
    
    try:
        jobs = await search_jobs_for_user(user_id)
        print(f"✅ Found {len(jobs)} jobs!")
        
        # Print first 3 jobs
        for i, job in enumerate(jobs[:3]):
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
    import sys
    
    if len(sys.argv) > 1:
        if sys.argv[1] == "search":
            # Run job search
            await daily_search()
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
            print("  python main.py search     - Run job search")
            print("  python main.py telegram   - Start Telegram bot")
            print("  python main.py setup      - Setup default user")
    else:
        # Default: run both
        print("JobBot - Automated Job Search")
        print("=" * 40)
        
        # Setup user
        await setup_user()
        
        # Search jobs
        await daily_search()
        
        print("\n" + "=" * 40)
        print("To use Telegram bot, run: python main.py telegram")


if __name__ == "__main__":
    asyncio.run(main())
