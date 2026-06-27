#!/usr/bin/env python3
"""JobScraper CLI."""
import click
import json
from rich.console import Console
from rich.table import Table
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

from src.db import init_db, get_session
from src.main import JobScraperOrchestrator
from src.db.models import PrepArtifact

console = Console()


@click.group()
def cli():
    """JobScraper - End-to-end job search and interview prep system."""
    pass


@cli.command()
def init():
    """Initialize the database."""
    console.print("[bold green]Initializing database...[/bold green]")
    init_db()
    console.print("[bold green]✓ Database initialized successfully[/bold green]")


@cli.command()
@click.option('--remote-only', is_flag=True, help='Load only remote companies')
@click.option('--chicago-only', is_flag=True, help='Load only Chicago companies')
def load_seeds(remote_only, chicago_only):
    """Load seed companies from CSV files."""
    orchestrator = JobScraperOrchestrator()

    if not chicago_only:
        console.print("[bold cyan]Loading remote companies...[/bold cyan]")
        count = orchestrator.load_seed_companies('data/seeds/remote_companies.csv')
        console.print(f"[green]✓ Loaded {count} remote companies[/green]")

    if not remote_only:
        console.print("[bold cyan]Loading Chicago companies...[/bold cyan]")
        count = orchestrator.load_seed_companies('data/seeds/chicago_companies.csv')
        console.print(f"[green]✓ Loaded {count} Chicago companies[/green]")


@cli.command()
def detect_ats():
    """Detect ATS type for all companies."""
    console.print("[bold cyan]Detecting ATS for companies...[/bold cyan]")
    orchestrator = JobScraperOrchestrator()
    count = orchestrator.detect_ats_for_companies()
    console.print(f"[green]✓ Detected ATS for {count} companies[/green]")


@cli.command()
@click.option('--company', help='Ingest jobs for specific company name')
def ingest(company):
    """Ingest jobs from all companies or a specific company."""
    orchestrator = JobScraperOrchestrator()

    if company:
        # Ingest for specific company
        console.print(f"[bold cyan]Ingesting jobs for {company}...[/bold cyan]")
        from src.db.models import Company
        comp = orchestrator.session.query(Company).filter_by(name=company).first()
        if not comp:
            console.print(f"[red]✗ Company not found: {company}[/red]")
            return
        count = orchestrator.ingest_jobs_for_company(comp)
        console.print(f"[green]✓ Ingested {count} jobs for {company}[/green]")
    else:
        # Full ingestion
        console.print("[bold cyan]Running full ingestion...[/bold cyan]")
        orchestrator.run_full_ingestion()
        console.print("[green]✓ Full ingestion completed[/green]")


@cli.command()
def score():
    """Score all eligible jobs."""
    console.print("[bold cyan]Scoring eligible jobs...[/bold cyan]")
    orchestrator = JobScraperOrchestrator()
    count = orchestrator.score_eligible_jobs()
    console.print(f"[green]✓ Scored {count} jobs[/green]")


@cli.command()
@click.option('--limit', default=25, help='Number of jobs to show')
@click.option('--min-score', default=70.0, help='Minimum score threshold')
def top(limit, min_score):
    """Show top ranked jobs."""
    orchestrator = JobScraperOrchestrator()
    jobs = orchestrator.get_top_jobs(limit=limit, min_score=min_score)

    if not jobs:
        console.print("[yellow]No jobs found matching criteria[/yellow]")
        return

    console.print(f"\n[bold cyan]Top {len(jobs)} Jobs (score ≥ {min_score})[/bold cyan]\n")

    table = Table(show_header=True, header_style="bold magenta")
    table.add_column("#", width=3)
    table.add_column("Score", width=6)
    table.add_column("Title", width=35)
    table.add_column("Company", width=20)
    table.add_column("Location", width=15)
    table.add_column("Salary", width=15)

    for idx, job in enumerate(jobs, 1):
        # Format salary
        if job['salary_min'] and job['salary_max']:
            salary = f"${job['salary_min']/1000:.0f}k-${job['salary_max']/1000:.0f}k"
        elif job['salary_min']:
            salary = f"${job['salary_min']/1000:.0f}k+"
        else:
            salary = "Unknown"

        # Format location
        location = "Remote" if job['is_remote'] else "Chicago" if job['is_chicago'] else job['location_raw'][:15]

        # Color-code score
        score = job['score']
        if score >= 85:
            score_str = f"[bold green]{score:.1f}[/bold green]"
        elif score >= 75:
            score_str = f"[green]{score:.1f}[/green]"
        else:
            score_str = f"[yellow]{score:.1f}[/yellow]"

        table.add_row(
            str(idx),
            score_str,
            job['title'][:35],
            job['company_name'][:20],
            location,
            salary
        )

    console.print(table)


@cli.command()
@click.argument('job_index', type=int)
def detail(job_index):
    """Show detailed view of a job by its index from top list."""
    orchestrator = JobScraperOrchestrator()
    jobs = orchestrator.get_top_jobs(limit=50)

    if job_index < 1 or job_index > len(jobs):
        console.print(f"[red]✗ Invalid job index. Must be between 1 and {len(jobs)}[/red]")
        return

    job = jobs[job_index - 1]

    # Display job details
    console.print(f"\n[bold cyan]{job['title']}[/bold cyan]")
    console.print(f"[bold]Company:[/bold] {job['company_name']}")
    console.print(f"[bold]Location:[/bold] {job['location_raw']}")
    console.print(f"[bold]Score:[/bold] {job['score']:.1f}/100")
    console.print(f"[bold]Apply URL:[/bold] {job['apply_url']}\n")

    # Show top reasons
    console.print("[bold]Top Reasons:[/bold]")
    for reason in job['top_reasons']:
        console.print(f"  • {reason}")

    console.print(f"\n[dim]Job PK: {job['job_pk']}[/dim]")


@cli.command()
@click.argument('job_pk')
def prep(job_pk):
    """Generate prep pack for a job."""
    console.print(f"[bold cyan]Generating prep pack for job {job_pk}...[/bold cyan]")
    orchestrator = JobScraperOrchestrator()

    prep_artifact = orchestrator.generate_prep_pack(job_pk)

    if prep_artifact:
        console.print("[green]✓ Prep pack generated successfully[/green]")
        console.print(f"\nUse 'jobscraper view-prep {job_pk}' to view the prep pack")
    else:
        console.print("[red]✗ Failed to generate prep pack[/red]")


@cli.command()
@click.argument('job_pk')
def view_prep(job_pk):
    """View prep pack for a job."""
    session = get_session()
    prep = session.query(PrepArtifact).filter_by(job_pk=job_pk).first()

    if not prep:
        console.print(f"[red]✗ No prep pack found for job {job_pk}[/red]")
        console.print(f"Generate one with: jobscraper prep {job_pk}")
        return

    # Parse JSON fields
    company_dossier = json.loads(prep.company_dossier_json or '{}')
    jd_spec = json.loads(prep.jd_structured_spec_json or '{}')
    fit_mapping = json.loads(prep.fit_mapping_json or '{}')
    interview_plan = json.loads(prep.predicted_interview_plan_json or '{}')
    study_plan = json.loads(prep.study_plan_json or '{}')

    # Company Dossier
    console.print("\n[bold cyan]═══ COMPANY DOSSIER ═══[/bold cyan]\n")
    console.print(f"[bold]Business Model:[/bold] {company_dossier.get('business_model_summary', 'N/A')}")
    console.print(f"[bold]Key Metrics:[/bold] {', '.join(company_dossier.get('key_metrics', []))}")

    # JD Spec
    console.print("\n[bold cyan]═══ JD STRUCTURED SPEC ═══[/bold cyan]\n")
    console.print(f"[bold]Role Family:[/bold] {jd_spec.get('role_family', 'N/A')}")
    console.print(f"[bold]Level:[/bold] {jd_spec.get('inferred_level', 'N/A')}")
    console.print("[bold]Must-Haves:[/bold]")
    for item in jd_spec.get('must_haves', [])[:5]:
        console.print(f"  • {item}")

    # Fit Mapping
    console.print("\n[bold cyan]═══ FIT MAPPING ═══[/bold cyan]\n")
    console.print("[bold]Positioning Angle:[/bold]")
    console.print(f"{fit_mapping.get('positioning_angle', 'N/A')}\n")
    console.print("[bold]Strongest Matches:[/bold]")
    for match in fit_mapping.get('strongest_matches', [])[:3]:
        console.print(f"  • {match.get('skill', 'N/A')}")

    # Interview Prediction
    console.print("\n[bold cyan]═══ PREDICTED INTERVIEW ROUNDS ═══[/bold cyan]\n")
    predicted_rounds = interview_plan.get('predicted_rounds', [])
    for round_info in predicted_rounds[:5]:
        likelihood = round_info.get('likelihood', 0)
        console.print(
            f"  • {round_info.get('round', 'N/A')} "
            f"[dim](likelihood: {likelihood*100:.0f}%)[/dim]"
        )

    # Study Plan
    console.print("\n[bold cyan]═══ 3-DAY CRAM PLAN ═══[/bold cyan]\n")
    three_day = study_plan.get('three_day_cram_plan', [])
    for day_plan in three_day:
        console.print(f"[bold]Day {day_plan.get('day', 'N/A')} ({day_plan.get('total_hours', 0)} hours):[/bold]")
        for task in day_plan.get('tasks', [])[:2]:
            console.print(f"  • {task.get('task', 'N/A')} ({task.get('duration_min', 0)} min)")

    # Day-of Cheat Sheet
    console.print("\n[bold cyan]═══ DAY-OF CHEAT SHEET ═══[/bold cyan]\n")
    cheatsheet = study_plan.get('day_of_cheatsheet', {})
    console.print(f"[bold]Role Positioning:[/bold] {cheatsheet.get('role_positioning', 'N/A')}")
    console.print(f"[bold]Likely First Question:[/bold] {cheatsheet.get('likely_first_question', 'N/A')}")


@cli.command()
def stats():
    """Show database statistics."""
    from src.db.models import Company, JobPosting, JobScore

    session = get_session()

    total_companies = session.query(Company).count()
    companies_with_ats = session.query(Company).filter(
        Company.ats_type.in_(['greenhouse', 'lever', 'ashby'])
    ).count()
    total_jobs = session.query(JobPosting).count()
    eligible_jobs = session.query(JobPosting).filter_by(is_eligible_location=True).count()
    scored_jobs = session.query(JobScore).count()

    console.print("\n[bold cyan]═══ DATABASE STATISTICS ═══[/bold cyan]\n")
    console.print(f"[bold]Total Companies:[/bold] {total_companies}")
    console.print(f"[bold]Companies with ATS Detected:[/bold] {companies_with_ats}")
    console.print(f"[bold]Total Jobs:[/bold] {total_jobs}")
    console.print(f"[bold]Eligible Jobs (Remote/Chicago):[/bold] {eligible_jobs}")
    console.print(f"[bold]Scored Jobs:[/bold] {scored_jobs}\n")


if __name__ == '__main__':
    cli()
