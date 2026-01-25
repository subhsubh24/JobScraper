## JobScraper Web Application

## Quick Start

### 1. Install Dependencies

```bash
cd /Users/subhmukherjee/PycharmProjects/JobScraper
source venv/bin/activate  # If not already activated
pip install -r requirements.txt
```

### 2. Set Up Environment

```bash
# Make sure .env has your OpenAI API key
cat .env | grep OPENAI_API_KEY
```

### 3. Initialize Database

```bash
python cli.py init
```

### 4. Start the Web App

```bash
python app.py
```

The app will start at: **http://127.0.0.1:5000**

Open your browser and navigate to that URL!

## Features

### 📊 Dashboard (Home)
- **Stats Overview**: Companies, jobs, eligible jobs, scored jobs
- **Top 10 Jobs**: Highest-ranked jobs today
- **Quick Actions**: View details, add to pipeline

**URL**: http://127.0.0.1:5000/

### 📋 All Jobs Page
- **Filters**: Score threshold, location (Remote/Chicago), role family
- **Sortable Table**: Score, title, company, salary, level
- **Quick Actions**: View details, apply directly

**URL**: http://127.0.0.1:5000/jobs

### 🔍 Job Detail Page
- **Complete Job Info**: Title, company, location, salary, description
- **Score Breakdown**: Visual breakdown of all 8 scoring components
- **Top Reasons**: Why this job scored high
- **Red Flags**: Potential concerns
- **Actions**:
  - Apply Now (opens job posting)
  - Add to Pipeline
  - Generate Prep Pack

**URL**: http://127.0.0.1:5000/job/{job_pk}

### 📚 Prep Pack Viewer
- **6 Comprehensive Tabs**:
  1. **Company Dossier**: Business model, metrics, competition
  2. **JD Spec**: Must-haves, nice-to-haves, interview format prediction
  3. **Fit Mapping**: Your strongest matches, STAR stories, gaps analysis
  4. **Interview Prediction**: Predicted rounds with likelihood
  5. **Question Bank**: 25-40 predicted questions with answer outlines
  6. **Study Plan**: 3-day + 7-day time-boxed plans, cheat sheet

**URL**: http://127.0.0.1:5000/job/{job_pk}/prep

### 📅 CRM Pipeline Board
- **Kanban-Style Board**: 11 stages from "Interested" to "Offer"
- **Cards Show**:
  - Job title + company
  - Next action
  - Due date (red if overdue)
- **Move Between Stages**: Click to update status
- **Rejected/Withdrawn**: Separate sections

**URL**: http://127.0.0.1:5000/pipeline

### ⚙️ Admin Panel
- **Actions**:
  - Load Seed Companies
  - Detect ATS
  - Run Ingestion (15-30 minutes)
  - Score Jobs
- **Stats**:
  - Companies by ATS type
  - Recent ingestions

**URL**: http://127.0.0.1:5000/admin

## Typical Workflow

### First Time Setup (10 minutes)

1. **Navigate to Admin Panel**: http://127.0.0.1:5000/admin

2. **Click Actions in Order**:
   - ① "Load Seed Companies" (2 seconds)
   - ② "Detect ATS" (1-2 minutes)
   - ③ "Run Ingestion" (15-30 minutes) ⏱️
   - ④ "Score Jobs" (1-2 minutes)

3. **Wait for ingestion to complete** (you'll see success message)

4. **Go to Dashboard**: See your top jobs!

### Daily Workflow (10 minutes/day)

**Morning**:
1. Open http://127.0.0.1:5000
2. Review "Top 10 Jobs Today"
3. Click jobs that interest you

**For Each Job**:
1. Click job → View detail page
2. Review score breakdown + red flags
3. Decision:
   - **Interested**: Click "Add to Pipeline"
   - **Very Interested**: Click "Generate Prep Pack"
   - **Not Interested**: Go back

**Prep Pack Generation**:
1. Takes ~90 seconds
2. Costs $0.07 (OpenAI API)
3. Click "View Prep Pack" when done
4. Read through all 6 tabs
5. Print/save "Day-Of Cheat Sheet"

**Pipeline Management**:
1. Go to Pipeline: http://127.0.0.1:5000/pipeline
2. Review cards with overdue actions (red)
3. Update status as you make progress
4. System auto-calculates next actions

### Weekly Refresh

1. Go to Admin: http://127.0.0.1:5000/admin
2. Click "Run Ingestion" (fetches new jobs)
3. Click "Score Jobs" (scores new jobs)
4. Review updated top jobs list

## Screenshots Guide

### Dashboard
```
┌─────────────────────────────────────────────────────┐
│ Dashboard                                            │
├─────────────────────────────────────────────────────┤
│  [82 Companies] [1,247 Jobs] [423 Eligible] [423...]│
│                                                      │
│  Top 10 Jobs Today                                  │
│  ┌────────────────────────────────────────────────┐ │
│  │ 87.3 │ Data Scientist │ Sift │ Remote │ ...   │ │
│  │ 85.1 │ Decision Sci   │ Stripe │ Remote │ ... │ │
│  └────────────────────────────────────────────────┘ │
└─────────────────────────────────────────────────────┘
```

### Job Detail
```
┌─────────────────────────────────────────────────────┐
│ Data Scientist at Sift                              │
├─────────────────────────────────────────────────────┤
│  Remote │ data_science │ senior │ Trading Firm      │
│  Salary: $160k - $190k │ Posted: 2026-01-15        │
│                                                      │
│  [Apply Now] [Add to Pipeline] [Generate Prep Pack] │
│                                                      │
│  Score: 87.3/100                                    │
│  ✓ Strong resume↔JD match (33/35)                  │
│  ✓ Title='Data Scientist' (10/10)                  │
│  ✓ Remote US (10/10)                               │
│                                                      │
│  Job Description...                                 │
└─────────────────────────────────────────────────────┘
```

### Prep Pack
```
┌─────────────────────────────────────────────────────┐
│ [Company] [JD] [Fit] [Interview] [Questions] [Study]│
├─────────────────────────────────────────────────────┤
│  Company Dossier                                    │
│  • Business Model: SaaS fraud detection...          │
│  • Key Metrics: Transaction volume, FPR...          │
│  • Competition: Arkose Labs, PerimeterX...          │
│                                                      │
│  [View all 6 tabs for complete prep pack]          │
└─────────────────────────────────────────────────────┘
```

### Pipeline Board
```
┌──────────┬──────────┬──────────┬──────────┐
│Interested│Outreach  │Applied   │Screen    │
│    (5)   │Queued (3)│   (8)    │   (2)    │
├──────────┼──────────┼──────────┼──────────┤
│ Job A    │ Job D    │ Job G    │ Job J    │
│ @ Co X   │ @ Co Y   │ @ Co Z   │ @ Co M   │
│ Next: ... │ Next:... │ Next:... │ Due: ... │
└──────────┴──────────┴──────────┴──────────┘
```

## API Endpoints

All API endpoints return JSON.

### Job Management

**Generate Prep Pack**:
```
POST /api/job/{job_pk}/generate-prep
Response: {"success": true, "message": "..."}
```

**Add to Pipeline**:
```
POST /api/job/{job_pk}/add-to-pipeline
Response: {"success": true, "message": "..."}
```

### Application Management

**Update Status**:
```
POST /api/application/{app_id}/update-status
Body: {"status": "applied"}
Response: {"success": true, "message": "..."}
```

### Admin Actions

**Load Seeds**:
```
POST /api/admin/load-seeds
Response: {"success": true, "message": "Loaded 82 companies"}
```

**Detect ATS**:
```
POST /api/admin/detect-ats
Response: {"success": true, "message": "Detected ATS for 68 companies"}
```

**Run Ingestion**:
```
POST /api/admin/ingest
Response: {"success": true, "message": "Ingestion completed"}
```

**Score Jobs**:
```
POST /api/admin/score
Response: {"success": true, "message": "Scored 423 jobs"}
```

## Keyboard Shortcuts

- **Ctrl+H**: Go to Dashboard
- **Ctrl+J**: Go to All Jobs
- **Ctrl+P**: Go to Pipeline
- **Ctrl+/**: Show shortcuts

## Troubleshooting

### Port already in use
```bash
# Check what's using port 5000
lsof -i :5000

# Kill the process or change port in app.py:
app.run(host='127.0.0.1', port=5001, debug=True)
```

### Can't access from other devices
```bash
# Change host to 0.0.0.0 in app.py:
app.run(host='0.0.0.0', port=5000, debug=True)
# Access from: http://<your-ip>:5000
```

### Database errors
```bash
# Reinitialize database
rm data/jobscraper.db
python cli.py init
```

### LLM errors
```bash
# Check API key
cat .env | grep OPENAI_API_KEY

# Test API key
python -c "from openai import OpenAI; client = OpenAI(); print('OK')"
```

### Slow page loads
```bash
# Add indexes if database gets large (>10k jobs)
# Or switch to PostgreSQL (edit DATABASE_URL in .env)
```

## Production Deployment

### Option 1: Local Production Server

```bash
# Install Gunicorn
pip install gunicorn

# Run with Gunicorn (better than Flask dev server)
gunicorn -w 4 -b 127.0.0.1:5000 app:app
```

### Option 2: Railway

```bash
# Create Procfile
echo "web: gunicorn app:app" > Procfile

# Push to Railway
railway init
railway up
```

### Option 3: Docker

```bash
# Create Dockerfile
cat > Dockerfile << 'EOF'
FROM python:3.9
WORKDIR /app
COPY requirements.txt .
RUN pip install -r requirements.txt
COPY . .
EXPOSE 5000
CMD ["gunicorn", "-w", "4", "-b", "0.0.0.0:5000", "app:app"]
EOF

# Build and run
docker build -t jobscraper .
docker run -p 5000:5000 --env-file .env jobscraper
```

## Security Notes

- **Secret Key**: Change `SECRET_KEY` in `.env` for production
- **API Key**: Never commit `.env` to git
- **Authentication**: Current version has no auth (localhost only)
- **HTTPS**: Use reverse proxy (nginx/Caddy) for production

## Performance Tips

- **Cache**: LLM responses are cached in `data/cache/`
- **Database**: Switch to PostgreSQL for >10k jobs
- **Background Jobs**: Use Celery for async prep pack generation
- **CDN**: Host static files on CDN for faster loads

## Cost Tracking

Monitor OpenAI API usage:
```bash
# Count prep packs generated
sqlite3 data/jobscraper.db "SELECT COUNT(*) FROM prep_artifact;"

# Estimated cost: COUNT × $0.07
```

Set up billing alerts in OpenAI dashboard: https://platform.openai.com/account/billing/overview

## Support

Issues? Questions?
- Check logs: `tail -f data/logs/*.log`
- Review docs: `README.md`, `QUICKSTART.md`
- Email: subh.mukherjee1996@gmail.com

---

**Enjoy your job search automation! 🚀**
