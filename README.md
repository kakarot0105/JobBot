# JobBot 🤖 - Automated Job Search

Find Data Engineering jobs across multiple platforms and get notified via Telegram.

## Features

✨ **Multi-Source Job Search**
- RemoteOK
- JustJoinIt
- GitHub Jobs
- Indeed (via RSS)

🔍 **Smart Filtering**
- Keywords: Data Engineer, Backend, etc.
- Location: USA, Remote, specific cities
- Salary range
- Experience level (Junior, Mid, Senior)
- Job type (Full-time, Contract)

💬 **Telegram Bot**
- `/start` - Initialize and set preferences
- Daily job digests
- Track applied jobs
- Job statistics

📊 **Database**
- SQLite job storage
- Applied job tracking
- Search history
- User preferences

## Setup

### 1. Clone & Install

```bash
cd /home/ubuntu/clawd/JobBot
python -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
```

### 2. Configure

```bash
cp .env.example .env
# Edit .env with your Telegram token
```

### 3. Run

**Search jobs once:**
```bash
python main.py search
```

**Start Telegram bot:**
```bash
python main.py telegram
```

**Setup default user:**
```bash
python main.py setup
```

## Configuration

Current setup for @banna:
- **Keywords:** Data Engineer
- **Location:** USA, Remote
- **Level:** Mid
- **Type:** Contract, Full-time
- **Salary:** Any

Edit in `main.py` DEFAULT_FILTERS to change.

## Job Sources

| Source | API | Status |
|--------|-----|--------|
| RemoteOK | ✅ Public API | Working |
| JustJoinIt | ✅ Public API | Working |
| GitHub Jobs | ✅ GitHub API | Working |
| Indeed | ⚠️ Requires API Key | Limited |

## Database Schema

**users** - Telegram user info  
**filters** - User preferences  
**jobs** - Job listings  
**applied_jobs** - Applied tracking  
**sent_jobs** - Telegram notification history  

## Daily Automation

Add to crontab for daily 9am search:

```bash
0 9 * * * cd /home/ubuntu/clawd/JobBot && source .venv/bin/activate && python main.py search
```

Or use OpenClaw cron:

```
Schedule: Daily 9am
Action: Run "python main.py search"
Notify: Telegram @banna
```

## Telegram Bot Commands

```
/start - Initialize bot
/search - Search for jobs now
/filters - Update preferences
/applied - View applied jobs
/stats - Job statistics
```

## Notes

- RemoteOK and JustJoinIt have public free APIs
- Indeed requires paid API access or RSS feed parsing
- Deduplication prevents duplicate job entries
- All jobs stored in SQLite database

## Future Features

- [ ] Weekly summary emails
- [ ] Salary trend analytics
- [ ] Machine learning job matching
- [ ] Multiple user support
- [ ] Web dashboard
- [ ] One-click apply links
- [ ] Interview tips from company reviews

---

Built for @banna | Data Engineer Jobs | Remote + USA
