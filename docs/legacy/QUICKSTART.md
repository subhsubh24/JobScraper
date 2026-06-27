# JobScraper Quick Start Guide

Get up and running with JobScraper in 10 minutes.

## Prerequisites

- Python 3.9+ installed
- OpenAI API key ([Get one here](https://platform.openai.com/api-keys))

## Installation

### Option 1: Automated Setup (Recommended)

```bash
# Run the setup script
./setup.sh

# Edit .env and add your OpenAI API key
nano .env  # or use your preferred editor
```

### Option 2: Manual Setup

```bash
# Create virtual environment
python3 -m venv venv
source venv/bin/activate

# Install dependencies
pip install -r requirements.txt

# Create .env file
cp .env.example .env
# Edit .env and add OPENAI_API_KEY

# Initialize database
python cli.py init
```

## First Run (5 minutes)

### 1. Test with a Single Company

```bash
# Load seed companies
python cli.py load-seeds

# Check stats
python cli.py stats

# Ingest jobs from a single company (fast test)
python cli.py detect-ats
python cli.py ingest --company "Sift"

# View results
python cli.py stats
python cli.py top --limit 5
```

### 2. Full Ingestion (15-30 minutes)

```bash
# Run full ingestion workflow
python cli.py ingest

# This will:
# - Load 80+ companies
# - Detect ATS for each
# - Fetch all jobs
# - Score all eligible jobs
```

### 3. Explore Top Jobs

```bash
# Show top 25 jobs
python cli.py top

# View job details (use index from top list)
python cli.py detail 1

# Generate prep pack
python cli.py prep <job_pk_from_detail_view>

# View prep pack
python cli.py view-prep <job_pk>
```

## Daily Workflow

Once set up, your daily workflow is:

```bash
# 1. Refresh jobs (run daily or weekly)
python cli.py ingest

# 2. View top jobs
python cli.py top

# 3. Generate prep packs for interesting jobs
python cli.py detail 1
python cli.py prep <job_pk>
python cli.py view-prep <job_pk>
```

## Configuration

Edit `.env` to customize:

```bash
# Required
OPENAI_API_KEY=sk-...

# Optional customization
TARGET_SALARY_MIN=160000
ALLOWED_ROLE_FAMILIES=data_science,decision_science,applied_science
```

## Troubleshooting

### "No module named 'src'"
```bash
# Make sure you're in the project root and venv is activated
cd /Users/subhmukherjee/PycharmProjects/JobScraper
source venv/bin/activate
```

### "OpenAI API key not found"
```bash
# Check that .env exists and has OPENAI_API_KEY set
cat .env | grep OPENAI_API_KEY
```

### "No jobs found"
```bash
# Check stats to see if jobs were ingested
python cli.py stats

# Check logs
tail -n 50 data/logs/main.log
```

### Rate limits or timeouts
```bash
# Ingest one company at a time
python cli.py ingest --company "Stripe"
python cli.py ingest --company "Datadog"
```

## Next Steps

- Read [README.md](README.md) for full documentation
- Customize seed companies in `data/seeds/`
- Explore database schema in `src/db/models.py`
- Check logs in `data/logs/` for debugging

## Support

Issues? Questions?
- Email: subh.mukherjee1996@gmail.com
- GitHub Issues: [Report a bug](https://github.com/yourusername/JobScraper/issues)

---

**Tip**: Run `python cli.py --help` to see all available commands.
