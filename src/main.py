"""Main orchestrator for JobScraper CLI operations."""
from typing import List
from sqlalchemy.orm import Session

from src.db.models import Company, JobPosting, ATSType
from src.ingestion.detector import ATSDetector
from src.ingestion.greenhouse import GreenhouseClient
from src.ingestion.lever import LeverClient


class JobScraperOrchestrator:
    """Orchestrates job scraping, ingestion, and scoring operations."""

    def __init__(self, db: Session):
        self.db = db
        self.detector = ATSDetector()

    def detect_ats_for_company(self, company: Company) -> Company:
        """Detect and update ATS type for a company."""
        if not company.careers_url:
            return company

        ats_type, identifier = self.detector.detect_from_careers_page(
            company.careers_url
        )

        company.ats_type = ats_type
        if identifier:
            company.ats_identifier = identifier

        self.db.flush()
        return company

    def detect_ats_for_all(self) -> List[Company]:
        """Detect ATS for all companies without one."""
        companies = self.db.query(Company).filter(
            Company.ats_type == ATSType.UNKNOWN,
            Company.careers_url.isnot(None),
            Company.is_active.is_(True),
        ).all()

        updated = []
        for company in companies:
            try:
                self.detect_ats_for_company(company)
                if company.ats_type != ATSType.UNKNOWN:
                    updated.append(company)
                    print(f"Detected {company.ats_type.value} for {company.name}")
            except Exception as e:
                print(f"Error detecting ATS for {company.name}: {e}")

        return updated

    def ingest_jobs_from_company(self, company: Company) -> List[JobPosting]:
        """Ingest all jobs from a company's ATS."""
        if company.ats_type == ATSType.UNKNOWN:
            print(f"Unknown ATS for {company.name}, skipping")
            return []

        if not company.ats_identifier:
            print(f"No ATS identifier for {company.name}, skipping")
            return []

        # Get appropriate client
        if company.ats_type == ATSType.GREENHOUSE:
            client = GreenhouseClient(company.ats_identifier)
        elif company.ats_type == ATSType.LEVER:
            client = LeverClient(company.ats_identifier)
        else:
            print(f"No client for {company.ats_type.value}")
            return []

        # Fetch jobs
        try:
            if company.ats_type == ATSType.GREENHOUSE:
                job_listings = client.fetch_all_with_details()
            else:
                job_listings = client.fetch_jobs()
        except Exception as e:
            print(f"Error fetching jobs from {company.name}: {e}")
            return []

        # Create or update job postings
        created_jobs = []
        for listing in job_listings:
            # Check if job already exists
            existing = self.db.query(JobPosting).filter(
                JobPosting.company_id == company.id,
                JobPosting.external_id == listing.external_id,
            ).first()

            if existing:
                # Update existing
                existing.title = listing.title
                existing.location = listing.location
                existing.description = listing.description
                existing.url = listing.url
                existing.remote_type = listing.remote_type
            else:
                # Create new
                job = JobPosting(
                    company_id=company.id,
                    company_name=company.name,
                    external_id=listing.external_id,
                    title=listing.title,
                    location=listing.location,
                    description=listing.description,
                    requirements=listing.requirements,
                    url=listing.url,
                    remote_type=listing.remote_type,
                )
                self.db.add(job)
                created_jobs.append(job)

        self.db.flush()
        print(f"Ingested {len(created_jobs)} new jobs from {company.name}")
        return created_jobs

    def ingest_all_companies(self) -> List[JobPosting]:
        """Ingest jobs from all active companies."""
        companies = self.db.query(Company).filter(
            Company.ats_type != ATSType.UNKNOWN,
            Company.ats_identifier.isnot(None),
            Company.is_active.is_(True),
        ).all()

        all_jobs = []
        for company in companies:
            jobs = self.ingest_jobs_from_company(company)
            all_jobs.extend(jobs)

        return all_jobs

    def get_stats(self) -> dict:
        """Get database statistics."""
        from src.db.models import User, Application, PrepArtifact

        return {
            "companies": self.db.query(Company).count(),
            "companies_with_ats": self.db.query(Company).filter(
                Company.ats_type != ATSType.UNKNOWN
            ).count(),
            "job_postings": self.db.query(JobPosting).count(),
            "users": self.db.query(User).count(),
            "applications": self.db.query(Application).count(),
            "prep_artifacts": self.db.query(PrepArtifact).count(),
        }
