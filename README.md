# JobBot - Automated Job Search 🤖

Multi-source job scraper with Telegram notifications for Data Engineers.

## Features
- 🔍 Scrapes jobs from **RemoteOK, JustJoinIt, GitHub Jobs**
- 📨 Sends to **Telegram group** daily at 9am EST
- 🎯 Filters: Data Engineer, Mid-level, USA+Remote, Contract+Full-time
- ✅ Real job data (no mock)

## Deploy to Railway

### Quick Setup (3 min)
1. Go to **https://railway.app**
2. Sign up with GitHub
3. Click **New Project** → **Deploy from GitHub repo**
4. Select `kakarot0105/JobBot`
5. Click **Deploy**

### Configure Environment Variables
Once deployed, add to Railway dashboard:
```
TELEGRAM_TOKEN=8431762614:AAEsckfl-0zPLMgt2QVrqOXBCsCpu3pftwA
```

### Schedule Daily Job (9am EST)
1. In Railway dashboard → **Job**
2. Create **Cron Job**:
   - Schedule: `0 14 * * *` (2pm UTC = 9am EST)
   - Command: `python main.py search`
   - Active: ✅

### Test Before Scheduling
```bash
python main.py search  # Real jobs
python main.py search --mock  # Mock data (sandbox)
```

## Local Development
```bash
python3 -m venv venv
source venv/bin/activate
pip install -r requirements.txt
TELEGRAM_TOKEN=<your-token> python main.py search
```

## Job Destinations
**Telegram Group:** Jobbot Alerts (`-1003357441031`)

Enjoy! 🚀
