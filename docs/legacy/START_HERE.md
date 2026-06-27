# 🚀 JobScraper - START HERE

## What You Have

A **complete web application** for automated job search with:
- ✅ Dashboard with top jobs
- ✅ Job listings with filters
- ✅ Detailed job view with score breakdown
- ✅ Prep pack generator (company dossier, interview questions, study plans)
- ✅ CRM pipeline board
- ✅ Admin panel for data ingestion

## Quick Start (5 minutes)

### 1. Run the Setup Script

```bash
cd /Users/subhmukherjee/PycharmProjects/JobScraper
./setup.sh
```

This will:
- Create virtual environment
- Install dependencies
- Initialize database
- Create .env file

### 2. Add Your OpenAI API Key

```bash
nano .env
```

Add your key:
```
OPENAI_API_KEY=sk-proj-your-key-here
```

Get a key here: https://platform.openai.com/api-keys

### 3. Start the Web App

```bash
./start_webapp.sh
```

### 4. Open Your Browser

Navigate to: **http://127.0.0.1:5000**

## First Time Setup (In the Web App)

1. **Go to Admin Panel**: Click "Admin" in the navigation bar

2. **Click these buttons in order**:
   - ① **Load Seed Companies** (2 seconds)
   - ② **Detect ATS** (1-2 minutes)
   - ③ **Run Ingestion** (15-30 minutes) ⏱️
   - ④ **Score Jobs** (1-2 minutes)

3. **Wait for ingestion** to complete (you'll see a success message)

4. **Go to Dashboard** and see your top jobs!

## Daily Workflow

### Morning (5 minutes)
1. Open http://127.0.0.1:5000
2. Review "Top 10 Jobs Today"
3. Click interesting jobs

### For Each Job (10 minutes)
1. View job details
2. Review score breakdown
3. **Interested?** → Click "Add to Pipeline"
4. **Very Interested?** → Click "Generate Prep Pack"

### Prep Pack (Read in 15 minutes)
- Company dossier
- JD spec with must-haves
- Your fit mapping
- 25-40 predicted interview questions
- 3-day + 7-day study plans
- Day-of cheat sheet

## Key Pages

| Page | URL | What It Does |
|------|-----|--------------|
| **Dashboard** | http://127.0.0.1:5000/ | Top 10 jobs + stats |
| **All Jobs** | http://127.0.0.1:5000/jobs | Full list with filters |
| **Job Detail** | http://127.0.0.1:5000/job/{id} | Score, description, prep pack |
| **Pipeline** | http://127.0.0.1:5000/pipeline | CRM board (Kanban) |
| **Admin** | http://127.0.0.1:5000/admin | Data ingestion controls |

## File Structure

```
JobScraper/
├── app.py                  # Flask web application ← START HERE
├── cli.py                  # Command-line interface (alternative)
├── start_webapp.sh         # Launch script ← USE THIS
├── setup.sh                # Installation script
│
├── templates/              # HTML templates
│   ├── index.html          # Dashboard
│   ├── jobs_list.html      # All jobs page
│   ├── job_detail.html     # Job detail + actions
│   ├── prep_pack.html      # Interview prep pack viewer
│   ├── pipeline.html       # CRM board
│   └── admin.html          # Admin panel
│
├── static/                 # CSS + JavaScript
│   ├── css/style.css
│   └── js/app.js
│
├── src/                    # Backend code
│   ├── main.py             # Orchestration
│   ├── db/                 # Database models
│   ├── ingestion/          # ATS APIs
│   ├── enrichment/         # LLM workflows
│   ├── ranking/            # Scoring engine
│   ├── crm/                # State machine
│   └── utils/              # Helpers
│
├── data/
│   ├── resume.txt          # Your resume
│   ├── seeds/              # Company lists
│   ├── jobscraper.db       # SQLite database (created on init)
│   ├── cache/              # LLM cache
│   └── logs/               # Application logs
│
└── Documentation
    ├── START_HERE.md       # This file
    ├── WEB_APP_GUIDE.md    # Detailed web app guide
    ├── README.md           # Full technical docs
    ├── QUICKSTART.md       # CLI quick start
    └── INSTALLATION_GUIDE.md
```

## How to Use

### Option 1: Web App (Recommended)

```bash
./start_webapp.sh
# Opens browser at http://127.0.0.1:5000
```

**Best for**:
- Visual interface
- Easy navigation
- Quick actions
- Viewing prep packs

### Option 2: Command Line

```bash
source venv/bin/activate
python cli.py top
python cli.py detail 1
python cli.py prep <job_pk>
```

**Best for**:
- Automation
- Scripting
- Quick checks

## Features Walkthrough

### 1. Dashboard
Shows overview of your job search:
- Total companies, jobs, eligible jobs
- Top 10 ranked jobs today
- Quick navigation

### 2. All Jobs Page
Browse all jobs with filters:
- Minimum score (70-100)
- Location (Remote/Chicago)
- Role family (Data Science, Decision Science, etc.)
- Sort by score

### 3. Job Detail Page
Complete information about a job:
- Title, company, location, salary
- **Score breakdown** with visual components
- **Top reasons** why it scored high
- **Red flags** to watch out for
- Actions: Apply, Add to Pipeline, Generate Prep Pack

### 4. Prep Pack Viewer
Comprehensive interview preparation:
- **Company Dossier**: Business model, metrics, competition
- **JD Spec**: Must-haves, nice-to-haves, interview format
- **Fit Mapping**: Your strengths, STAR stories, gaps
- **Interview Prediction**: Likely rounds + questions
- **Question Bank**: 25-40 questions with answer outlines
- **Study Plan**: Time-boxed 3-day + 7-day plans

### 5. CRM Pipeline Board
Track your applications:
- Kanban board with 11 stages
- Cards show job, company, next action
- Automatic next-action calculation
- Due date tracking (red if overdue)

### 6. Admin Panel
System management:
- Load seed companies
- Detect ATS types
- Run full ingestion (fetch jobs)
- Score all jobs
- View stats

## Cost

- **Setup**: Free
- **Monthly**: $50-70 (OpenAI API for prep packs)
- **Per Prep Pack**: $0.07 (cached and reusable)

## Troubleshooting

### Can't start the app
```bash
# Check if port 5000 is in use
lsof -i :5000

# Kill process if needed
kill -9 <PID>

# Or use different port (edit app.py line 259)
```

### No jobs showing
```bash
# Run ingestion from command line
python cli.py load-seeds
python cli.py detect-ats
python cli.py ingest
python cli.py score
```

### Prep pack generation fails
```bash
# Check API key
cat .env | grep OPENAI_API_KEY

# Test API connection
python -c "from openai import OpenAI; client = OpenAI(); print('✓ API key valid')"
```

### Database errors
```bash
# Reinitialize database
rm data/jobscraper.db
python cli.py init
```

## Tips

1. **Run ingestion weekly** to get new jobs
2. **Generate prep packs** only for jobs you're serious about (costs $0.07 each)
3. **Use filters** on All Jobs page to find specific types
4. **Check Pipeline** daily for next actions
5. **Keyboard shortcuts**: Ctrl+H (home), Ctrl+J (jobs), Ctrl+P (pipeline)

## Next Steps

After initial setup:

1. **Customize seed companies**: Edit `data/seeds/*.csv`
2. **Adjust scoring**: Edit `src/ranking/scorer.py`
3. **Tune LLM prompts**: Edit `src/enrichment/llm_workflows.py`
4. **Add more companies**: Update CSV and re-run ingestion

## Documentation

- **WEB_APP_GUIDE.md** → Detailed web app documentation
- **README.md** → Full technical documentation
- **QUICKSTART.md** → CLI quick start guide
- **SYSTEM_OVERVIEW.md** → Architecture deep-dive

## Support

Need help?
- Check logs: `tail -f data/logs/*.log`
- Run tests: `python -m pytest tests/ -v`
- Email: subh.mukherjee1996@gmail.com

---

## Summary

You now have a **complete web application** that:
1. ✅ Automatically fetches jobs from 80+ companies
2. ✅ Filters by Remote/Chicago + Data Science roles
3. ✅ Scores 0-100 with explainable breakdown
4. ✅ Generates comprehensive interview prep packs
5. ✅ Tracks applications in CRM pipeline
6. ✅ Costs $50-70/month (OpenAI API)

**Start here**: `./start_webapp.sh` → Open http://127.0.0.1:5000 → Go to Admin → Click buttons → View your jobs!

**🎉 Enjoy your automated job search!**
