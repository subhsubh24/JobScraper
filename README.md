# JobScraper

**End-to-end Job Search + Outreach CRM + Interview Prep System**

JobScraper is a comprehensive system designed to maximize interview conversion for Data Scientists targeting Remote/Chicago roles at $160k+. It automatically ingests jobs from ATS feeds, filters by location and role, ranks by fit, and generates tailored interview prep packs with predicted questions, study plans, and outreach templates.

## Features

- **Automated Job Ingestion**: Fetches jobs from Greenhouse, Lever, and Ashby APIs across 80+ companies
- **Smart Filtering**: Hard gates on location (Remote US or Chicago only) and role family
- **Intelligent Ranking**: Scores jobs 0-100 using resume↔JD embeddings, seniority fit, and domain alignment
- **Trading Mode**: Special scoring logic for trading firms (prefers analytics/decision science over quant research)
- **Interview Prep Packs**: Auto-generates company dossiers, predicted interview questions, and time-boxed study plans
- **Outreach Automation**: Pre-written recruiter messages, follow-up templates, and LinkedIn search queries
- **CRM Pipeline**: Tracks application status, next actions, and automated reminders

## Architecture

```
┌─────────────────────────────────────────────────────────────────┐
│                        CLI Interface                             │
└─────────────────────────────────────────────────────────────────┘
                                │
                                ▼
┌─────────────────────────────────────────────────────────────────┐
│                    Orchestration Layer                           │
│  Ingestion | Enrichment | Scoring | CRM | Prep Pack Generation  │
└─────────────────────────────────────────────────────────────────┘
                                │
                    ┌───────────┼───────────┐
                    ▼           ▼           ▼
        ┌───────────────┐  ┌────────────┐  ┌──────────────┐
        │  ATS APIs     │  │  LLM       │  │  Embeddings  │
        │  (GH/Lever/   │  │  Workflows │  │  (Sentence   │
        │   Ashby)      │  │  (GPT-4o)  │  │  Transform.) │
        └───────────────┘  └────────────┘  └──────────────┘
                                │
                                ▼
┌─────────────────────────────────────────────────────────────────┐
│                    Database (SQLite/Postgres)                    │
│  Company | JobPosting | JobScore | PrepArtifact | Application   │
└─────────────────────────────────────────────────────────────────┘
```

## Setup

### Prerequisites

- Python 3.9+
- OpenAI API key (for LLM workflows)
- pip

### Installation

1. Clone the repository:
```bash
cd /Users/subhmukherjee/PycharmProjects/JobScraper
```

2. Create virtual environment and install dependencies:
```bash
python3 -m venv venv
source venv/bin/activate  # On Windows: venv\Scripts\activate
pip install -r requirements.txt
```

3. Set up environment variables:
```bash
cp .env.example .env
# Edit .env and add your OPENAI_API_KEY
```

4. Initialize the database:
```bash
python cli.py init
```

## Quick Start

### Step 1: Load Seed Companies and Ingest Jobs

```bash
# Run full ingestion workflow (loads companies, detects ATS, ingests jobs, scores)
python cli.py ingest
```

This will:
- Load 50+ remote tech companies and 30+ Chicago companies
- Detect ATS type (Greenhouse, Lever, Ashby)
- Fetch all jobs from each company
- Parse location, salary, and role
- Filter by eligibility (Remote US or Chicago only)
- Score all eligible jobs

**Expected time**: 15-30 minutes for full ingestion (depends on API rate limits)

### Step 2: View Top Jobs

```bash
# Show top 25 jobs with score ≥ 70
python cli.py top

# Show top 10 jobs with score ≥ 80
python cli.py top --limit 10 --min-score 80
```

Output:
```
Top 25 Jobs (score ≥ 70)

  #  Score  Title                             Company              Location        Salary
────────────────────────────────────────────────────────────────────────────────────────────
  1  87.3   Data Scientist                    Sift                 Remote          $160k-$190k
  2  85.1   Decision Scientist, GTM           Stripe               Remote          $170k-$200k
  3  82.4   Data Scientist, Product           Amplitude            Remote          $150k-$180k
  ...
```

### Step 3: View Job Details

```bash
# View details for job #1 from top list
python cli.py detail 1
```

### Step 4: Generate Prep Pack

```bash
# Get job_pk from detail view, then generate prep pack
python cli.py prep <job_pk>

# View the prep pack
python cli.py view-prep <job_pk>
```

The prep pack includes:
- **Company Dossier**: Business model, key metrics, competitive landscape
- **JD Structured Spec**: Must-haves, nice-to-haves, predicted interview format
- **Fit Mapping**: Your strongest resume matches + recommended STAR stories
- **Interview Prediction**: 25-40 likely questions with answer outlines
- **Study Plan**: 3-day cram (6-8 hours) + 7-day plan (12-18 hours)
- **Outreach Pack**: Pre-written recruiter DM, email, follow-up messages

### Step 5: Database Stats

```bash
python cli.py stats
```

Output:
```
═══ DATABASE STATISTICS ═══

Total Companies: 82
Companies with ATS Detected: 68
Total Jobs: 1,247
Eligible Jobs (Remote/Chicago): 423
Scored Jobs: 423
```

## CLI Commands Reference

| Command | Description |
|---------|-------------|
| `python cli.py init` | Initialize database schema |
| `python cli.py load-seeds [--remote-only] [--chicago-only]` | Load seed companies from CSV |
| `python cli.py detect-ats` | Detect ATS type for all companies |
| `python cli.py ingest [--company NAME]` | Ingest jobs (all or specific company) |
| `python cli.py score` | Score all eligible jobs |
| `python cli.py top [--limit N] [--min-score X]` | Show top ranked jobs |
| `python cli.py detail INDEX` | Show detailed view of job by index |
| `python cli.py prep JOB_PK` | Generate prep pack for job |
| `python cli.py view-prep JOB_PK` | View prep pack for job |
| `python cli.py stats` | Show database statistics |

## Configuration

Edit `.env` to customize:

```bash
# OpenAI API Key (required)
OPENAI_API_KEY=your_key_here

# Database
DATABASE_URL=sqlite:///data/jobscraper.db

# LLM Settings
LLM_MODEL=gpt-4o
LLM_TEMPERATURE=0.3

# User Preferences
TARGET_SALARY_MIN=160000
ALLOWED_ROLE_FAMILIES=data_science,decision_science,applied_science,analytics_engineering
```

## Project Structure

```
JobScraper/
├── cli.py                      # CLI interface
├── src/
│   ├── db/
│   │   ├── models.py           # SQLAlchemy models
│   │   └── __init__.py
│   ├── ingestion/
│   │   ├── ats_detector.py     # Detect ATS from careers URL
│   │   ├── greenhouse.py       # Greenhouse API client
│   │   ├── lever.py            # Lever API client
│   │   ├── ashby.py            # Ashby API client
│   │   └── normalizer.py       # Job normalization
│   ├── enrichment/
│   │   ├── location_parser.py  # Location eligibility filtering
│   │   ├── salary_parser.py    # Salary extraction
│   │   ├── role_classifier.py  # Role family classification
│   │   └── llm_workflows.py    # LLM-powered workflows
│   ├── ranking/
│   │   └── scorer.py           # Job scoring engine
│   ├── crm/
│   │   └── state_machine.py    # Application status transitions
│   ├── utils/
│   │   ├── logger.py           # Logging utility
│   │   └── cache.py            # LLM response caching
│   └── main.py                 # Orchestration layer
├── data/
│   ├── seeds/
│   │   ├── remote_companies.csv
│   │   └── chicago_companies.csv
│   ├── resume.txt              # Your resume (pre-loaded)
│   ├── cache/                  # LLM response cache
│   └── logs/                   # Application logs
├── requirements.txt
├── .env.example
└── README.md
```

## Scoring Breakdown

Jobs are scored 0-100 across 8 components:

| Component | Max Points | Description |
|-----------|------------|-------------|
| Resume↔JD Match | 35 | Embedding similarity + keyword boost |
| Seniority Alignment | 12 | Prefers mid/senior for conversion |
| Title Preference | 10 | "Data Scientist" highest |
| Location Quality | 10 | Remote US best, Chicago good |
| Compensation Signal | 10 | ≥$160k gets full points |
| Role Authenticity | 8 | Penalizes dashboard-only roles |
| Recency | 5 | Newer postings ranked higher |
| Company Quality | 10 | User-defined priority companies |

**Trading Mode** adds:
- **Transition Feasibility** (+15 to -10): Prefers analytics/decision science, penalizes quant research/low-latency

## Location Hard Gates

Jobs are **automatically discarded** if:
- Not Remote US **AND** not Chicago
- Remote but explicitly excludes Illinois

**Eligible locations**:
- ✅ Remote US (no state restrictions)
- ✅ Remote US (excludes some states, but IL allowed)
- ✅ Chicago (onsite, hybrid, or remote)
- ❌ Remote US (excludes IL)
- ❌ San Francisco onsite
- ❌ New York hybrid

## LLM Workflows

6 LLM workflows power the prep pack generation:

1. **JD Parsing** → Structured spec (role family, level, must-haves, interview format prediction)
2. **Fit Mapping** → Resume↔JD matches, recommended STAR stories, gaps
3. **Company Dossier** → Business model, metrics, competitive landscape
4. **Interview Prediction** → Predicted rounds + 25-40 questions with answer outlines
5. **Study Plan** → Time-boxed 3-day/7-day plans + drills + cheat sheet
6. **Outreach Pack** → Recruiter DM, email, follow-up templates

**Cost**: ~$0.07 per job for all 6 workflows (cached aggressively)

## Adding More Companies

Edit `data/seeds/remote_companies.csv` or `data/seeds/chicago_companies.csv`:

```csv
name,careers_url,industry_tags
Your Company,https://yourcompany.com/careers,saas,analytics
```

Then run:
```bash
python cli.py load-seeds
python cli.py detect-ats
python cli.py ingest --company "Your Company"
```

## Troubleshooting

### No jobs found after ingestion
- Check `python cli.py stats` to see if jobs were ingested
- Verify ATS detection: companies with `ats_type='unknown'` won't be ingested
- Check logs in `data/logs/`

### LLM workflows failing
- Verify `OPENAI_API_KEY` is set in `.env`
- Check API quota and rate limits
- Review logs in `data/logs/llm_workflows.log`

### Scoring seems off
- Scoring weights are in `src/ranking/scorer.py`
- Resume embedding is based on `data/resume.txt` (update if needed)
- Check score breakdown with `python cli.py detail INDEX`

## Roadmap

- [ ] Web UI (Flask dashboard)
- [ ] CRM pipeline board with drag-and-drop
- [ ] Interview scheduling and reminders
- [ ] Feedback loop (learn from outcomes)
- [ ] Outreach tracking and analytics
- [ ] Automated follow-ups
- [ ] Browser extension for one-click add
- [ ] Mobile app

## Cost Estimates

**Monthly cost** (assuming 25 jobs shortlisted per day):
- OpenAI API: $51/month (25 jobs × $0.07 × 30 days)
- Hosting (if deployed): $10-20/month
- **Total**: ~$60-70/month

**Per-job cost**:
- LLM workflows: $0.07
- Embeddings: $0 (runs locally)

## License

MIT License - see LICENSE file

## Contributing

Contributions welcome! Please open an issue or PR.

## Support

For issues or questions:
- GitHub Issues: [Create an issue](https://github.com/yourusername/JobScraper/issues)
- Email: subh.mukherjee1996@gmail.com

---

**Built with**: Python, SQLAlchemy, OpenAI GPT-4o, Sentence Transformers, Click, Rich

**Optimized for**: Interview conversion and reduced cognitive load
