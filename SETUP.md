# JobBot Setup Guide

## Quick Start (No Manual Token Needed!)

Since you're using OpenClaw, Telegram is **already configured**. Just set up daily job search notifications:

### Option 1: OpenClaw Cron (Recommended)

I'll set up a daily 9am job search that sends results to Telegram via OpenClaw:

```bash
# This will be configured automatically
Schedule: Daily 9:00 AM
Task: Search for Data Engineer jobs
Deliver: Telegram notification to @banna
```

### Option 2: Manual Cron

Add to your system crontab:

```bash
# Daily at 9am
0 9 * * * cd /home/ubuntu/clawd/JobBot && source .venv/bin/activate && python3 main.py search >> /tmp/jobbot.log 2>&1
```

### Option 3: Run Now

Search for jobs immediately:

```bash
cd /home/ubuntu/clawd/JobBot
source .venv/bin/activate
python3 main.py search
```

## What It Does

1. **Searches** RemoteOK, JustJoinIt, GitHub for "Data Engineer" jobs
2. **Filters** by: USA + Remote, Mid-level, Contract + Full-time
3. **Deduplicates** to avoid showing same job twice
4. **Stores** in SQLite database
5. **Sends** digest via Telegram (if configured with OpenClaw)

## Configuration

Your settings (saved in database):
- **Keywords:** Data Engineer
- **Location:** USA, Remote
- **Level:** Mid
- **Type:** Contract, Full-time
- **Salary:** Any

To change filters, edit `main.py` DEFAULT_FILTERS section and run:
```bash
python3 main.py setup
```

## Database

Jobs are stored in `/tmp/jobbot.db`:

```
users          - Your profile
filters        - Job preferences
jobs           - All job listings
applied_jobs   - Jobs you've applied to
sent_jobs      - Jobs already notified
```

## OpenClaw Integration

Since OpenClaw has Telegram configured, JobBot can:
- ✅ Use OpenClaw's Telegram token
- ✅ Send notifications via OpenClaw message API
- ✅ Schedule via OpenClaw cron
- ✅ Track sent jobs to avoid duplicates

## Next Steps

1. Test search: `python3 main.py search`
2. Set up daily automation (see options above)
3. Jobs will be sent to your Telegram @banna every day

## Troubleshooting

**No jobs found?**
- Check internet connection
- API endpoints may be rate-limited
- Try again in a few minutes

**Duplicate jobs?**
- Database deduplication uses URL as unique key
- Check `applied_jobs` and `sent_jobs` tables

**Want to change keywords?**
Edit `main.py` DEFAULT_FILTERS and run `python3 main.py setup`

---

That's it! Jobs will start flowing to your Telegram daily. 🚀
