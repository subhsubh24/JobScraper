#!/usr/bin/env python3
"""JobScraper Flask Web Application."""
import os
import json
from datetime import datetime
from flask import Flask, render_template, request, jsonify, redirect, url_for
from dotenv import load_dotenv

load_dotenv()

from src.db import get_session, init_db
from src.db.models import (
    Company, JobPosting, JobScore, PrepArtifact,
    Application, Contact, OutreachSequence
)
from src.main import JobScraperOrchestrator
from src.crm import CRMStateMachine

app = Flask(__name__)
app.config['SECRET_KEY'] = os.getenv('SECRET_KEY', 'dev-secret-key-change-in-production')


@app.route('/')
def index():
    """Dashboard home page."""
    session = get_session()

    # Get stats
    total_companies = session.query(Company).count()
    total_jobs = session.query(JobPosting).count()
    eligible_jobs = session.query(JobPosting).filter_by(is_eligible_location=True).count()
    scored_jobs = session.query(JobScore).count()
    applications = session.query(Application).count()

    # Get top 10 jobs
    top_jobs_query = session.query(JobPosting, JobScore, Company).join(
        JobScore, JobPosting.job_pk == JobScore.job_pk
    ).join(
        Company, JobPosting.company_id == Company.company_id
    ).filter(
        JobScore.total_score >= 70
    ).order_by(
        JobScore.total_score.desc()
    ).limit(10).all()

    top_jobs = []
    for job, score, company in top_jobs_query:
        top_jobs.append({
            'job_pk': job.job_pk,
            'title': job.title,
            'company_name': company.name,
            'location_raw': job.location_raw,
            'is_remote': job.is_remote,
            'is_chicago': job.is_chicago,
            'salary_min': job.salary_min,
            'salary_max': job.salary_max,
            'score': score.total_score,
            'posted_at': job.posted_at.strftime('%Y-%m-%d') if job.posted_at else 'Unknown'
        })

    stats = {
        'total_companies': total_companies,
        'total_jobs': total_jobs,
        'eligible_jobs': eligible_jobs,
        'scored_jobs': scored_jobs,
        'applications': applications
    }

    return render_template('index.html', stats=stats, top_jobs=top_jobs)


@app.route('/jobs')
def jobs_list():
    """All jobs listing with filters."""
    session = get_session()

    # Get filter parameters
    min_score = float(request.args.get('min_score', 70))
    location_filter = request.args.get('location', 'all')
    role_filter = request.args.get('role', 'all')
    limit = int(request.args.get('limit', 50))

    # Build query
    query = session.query(JobPosting, JobScore, Company).join(
        JobScore, JobPosting.job_pk == JobScore.job_pk
    ).join(
        Company, JobPosting.company_id == Company.company_id
    ).filter(
        JobScore.total_score >= min_score
    )

    # Apply filters
    if location_filter == 'remote':
        query = query.filter(JobPosting.is_remote == True)
    elif location_filter == 'chicago':
        query = query.filter(JobPosting.is_chicago == True)

    if role_filter != 'all':
        query = query.filter(JobPosting.role_family == role_filter)

    # Get results
    results = query.order_by(JobScore.total_score.desc()).limit(limit).all()

    jobs = []
    for job, score, company in results:
        jobs.append({
            'job_pk': job.job_pk,
            'title': job.title,
            'company_name': company.name,
            'location_raw': job.location_raw,
            'is_remote': job.is_remote,
            'is_chicago': job.is_chicago,
            'salary_min': job.salary_min,
            'salary_max': job.salary_max,
            'role_family': job.role_family,
            'level_inferred': job.level_inferred,
            'score': score.total_score,
            'mode': score.mode,
            'posted_at': job.posted_at.strftime('%Y-%m-%d') if job.posted_at else 'Unknown',
            'apply_url': job.apply_url
        })

    return render_template('jobs_list.html', jobs=jobs,
                         min_score=min_score, location_filter=location_filter,
                         role_filter=role_filter)


@app.route('/job/<job_pk>')
def job_detail(job_pk):
    """Job detail page."""
    session = get_session()

    # Get job with score and company
    result = session.query(JobPosting, JobScore, Company).join(
        JobScore, JobPosting.job_pk == JobScore.job_pk
    ).join(
        Company, JobPosting.company_id == Company.company_id
    ).filter(
        JobPosting.job_pk == job_pk
    ).first()

    if not result:
        return "Job not found", 404

    job, score, company = result

    # Parse score breakdown
    breakdown = json.loads(score.score_breakdown_json)
    top_reasons = json.loads(score.top_reasons) if score.top_reasons else []
    red_flags = json.loads(score.red_flags) if score.red_flags else []

    # Check if prep pack exists
    prep_pack = session.query(PrepArtifact).filter_by(job_pk=job_pk).first()

    # Check if application exists
    application = session.query(Application).filter_by(job_pk=job_pk).first()

    job_data = {
        'job_pk': job.job_pk,
        'title': job.title,
        'company_name': company.name,
        'company_id': company.company_id,
        'location_raw': job.location_raw,
        'is_remote': job.is_remote,
        'is_chicago': job.is_chicago,
        'salary_min': job.salary_min,
        'salary_max': job.salary_max,
        'role_family': job.role_family,
        'level_inferred': job.level_inferred,
        'description_text': job.description_text,
        'apply_url': job.apply_url,
        'posted_at': job.posted_at.strftime('%Y-%m-%d') if job.posted_at else 'Unknown',
        'score': score.total_score,
        'mode': score.mode,
        'breakdown': breakdown,
        'top_reasons': top_reasons,
        'red_flags': red_flags,
        'has_prep_pack': prep_pack is not None,
        'has_application': application is not None,
        'application_status': application.status if application else None
    }

    return render_template('job_detail.html', job=job_data)


@app.route('/job/<job_pk>/prep')
def job_prep_pack(job_pk):
    """View prep pack for a job."""
    session = get_session()

    # Get job
    job = session.query(JobPosting).filter_by(job_pk=job_pk).first()
    if not job:
        return "Job not found", 404

    # Get prep pack
    prep = session.query(PrepArtifact).filter_by(job_pk=job_pk).first()
    if not prep:
        return redirect(url_for('job_detail', job_pk=job_pk))

    # Parse JSON fields
    company_dossier = json.loads(prep.company_dossier_json or '{}')
    jd_spec = json.loads(prep.jd_structured_spec_json or '{}')
    fit_mapping = json.loads(prep.fit_mapping_json or '{}')
    interview_plan = json.loads(prep.predicted_interview_plan_json or '{}')
    question_bank = json.loads(prep.question_bank_json or '[]')
    study_plan = json.loads(prep.study_plan_json or '{}')

    # Get company
    company = session.query(Company).filter_by(company_id=job.company_id).first()

    prep_data = {
        'job_pk': job_pk,
        'job_title': job.title,
        'company_name': company.name,
        'company_dossier': company_dossier,
        'jd_spec': jd_spec,
        'fit_mapping': fit_mapping,
        'interview_plan': interview_plan,
        'question_bank': question_bank,
        'study_plan': study_plan,
        'generated_at': prep.generated_at.strftime('%Y-%m-%d %H:%M') if prep.generated_at else 'Unknown'
    }

    return render_template('prep_pack.html', prep=prep_data)


@app.route('/api/job/<job_pk>/generate-prep', methods=['POST'])
def generate_prep_pack(job_pk):
    """Generate prep pack for a job (async)."""
    orchestrator = JobScraperOrchestrator()

    try:
        prep_artifact = orchestrator.generate_prep_pack(job_pk)
        if prep_artifact:
            return jsonify({'success': True, 'message': 'Prep pack generated successfully'})
        else:
            return jsonify({'success': False, 'message': 'Failed to generate prep pack'}), 500
    except Exception as e:
        return jsonify({'success': False, 'message': str(e)}), 500


@app.route('/pipeline')
def pipeline():
    """CRM pipeline board."""
    session = get_session()

    # Get all applications grouped by status
    applications = session.query(Application, JobPosting, Company).join(
        JobPosting, Application.job_pk == JobPosting.job_pk
    ).join(
        Company, JobPosting.company_id == Company.company_id
    ).all()

    # Group by status
    pipeline_data = {
        'interested': [],
        'outreach_queued': [],
        'outreach_sent': [],
        'applied': [],
        'screen': [],
        'tech_screen': [],
        'onsite': [],
        'final': [],
        'offer': [],
        'rejected': [],
        'withdrawn': []
    }

    for app, job, company in applications:
        card = {
            'application_id': app.application_id,
            'job_pk': job.job_pk,
            'title': job.title,
            'company_name': company.name,
            'status': app.status,
            'next_action': app.next_action,
            'next_action_due_at': app.next_action_due_at.strftime('%Y-%m-%d') if app.next_action_due_at else None,
            'is_overdue': app.next_action_due_at and app.next_action_due_at < datetime.utcnow() if app.next_action_due_at else False
        }
        pipeline_data[app.status].append(card)

    # Count per stage
    counts = {status: len(cards) for status, cards in pipeline_data.items()}

    return render_template('pipeline.html', pipeline=pipeline_data, counts=counts)


@app.route('/api/job/<job_pk>/add-to-pipeline', methods=['POST'])
def add_to_pipeline(job_pk):
    """Add job to CRM pipeline."""
    session = get_session()

    # Check if already in pipeline
    existing = session.query(Application).filter_by(job_pk=job_pk).first()
    if existing:
        return jsonify({'success': False, 'message': 'Job already in pipeline'}), 400

    # Create application
    app = Application(
        job_pk=job_pk,
        status='interested',
        next_action='Generate outreach pack and queue outreach',
        next_action_due_at=datetime.utcnow()
    )
    session.add(app)
    session.commit()

    return jsonify({'success': True, 'message': 'Added to pipeline'})


@app.route('/api/application/<int:app_id>/update-status', methods=['POST'])
def update_application_status(app_id):
    """Update application status."""
    session = get_session()

    app = session.query(Application).filter_by(application_id=app_id).first()
    if not app:
        return jsonify({'success': False, 'message': 'Application not found'}), 404

    new_status = request.json.get('status')

    # Validate transition
    success, message, next_action, next_action_due = CRMStateMachine.transition(
        app.status, new_status
    )

    if not success:
        return jsonify({'success': False, 'message': message}), 400

    # Update application
    app.status = new_status
    app.status_updated_at = datetime.utcnow()
    app.next_action = next_action
    app.next_action_due_at = next_action_due
    session.commit()

    return jsonify({'success': True, 'message': message})


@app.route('/admin')
def admin():
    """Admin panel for system management."""
    session = get_session()

    # Get stats
    companies_by_ats = session.query(
        Company.ats_type,
        session.query(Company).filter(Company.ats_type == Company.ats_type).count()
    ).group_by(Company.ats_type).all()

    recent_ingestions = session.query(Company).order_by(Company.updated_at.desc()).limit(10).all()

    stats = {
        'companies_by_ats': dict(companies_by_ats) if companies_by_ats else {},
        'recent_ingestions': [
            {
                'name': c.name,
                'ats_type': c.ats_type,
                'updated_at': c.updated_at.strftime('%Y-%m-%d %H:%M') if c.updated_at else 'Never'
            }
            for c in recent_ingestions
        ]
    }

    return render_template('admin.html', stats=stats)


@app.route('/api/admin/load-seeds', methods=['POST'])
def api_load_seeds():
    """Load seed companies."""
    try:
        orchestrator = JobScraperOrchestrator()
        count_remote = orchestrator.load_seed_companies('data/seeds/remote_companies.csv')
        count_chicago = orchestrator.load_seed_companies('data/seeds/chicago_companies.csv')
        return jsonify({
            'success': True,
            'message': f'Loaded {count_remote + count_chicago} companies'
        })
    except Exception as e:
        return jsonify({'success': False, 'message': str(e)}), 500


@app.route('/api/admin/detect-ats', methods=['POST'])
def api_detect_ats():
    """Detect ATS for all companies."""
    try:
        orchestrator = JobScraperOrchestrator()
        count = orchestrator.detect_ats_for_companies()
        return jsonify({
            'success': True,
            'message': f'Detected ATS for {count} companies'
        })
    except Exception as e:
        return jsonify({'success': False, 'message': str(e)}), 500


@app.route('/api/admin/ingest', methods=['POST'])
def api_ingest():
    """Run full ingestion."""
    try:
        orchestrator = JobScraperOrchestrator()
        orchestrator.run_full_ingestion()
        return jsonify({
            'success': True,
            'message': 'Ingestion completed successfully'
        })
    except Exception as e:
        return jsonify({'success': False, 'message': str(e)}), 500


@app.route('/api/admin/score', methods=['POST'])
def api_score():
    """Score all eligible jobs."""
    try:
        orchestrator = JobScraperOrchestrator()
        count = orchestrator.score_eligible_jobs()
        return jsonify({
            'success': True,
            'message': f'Scored {count} jobs'
        })
    except Exception as e:
        return jsonify({'success': False, 'message': str(e)}), 500


@app.route('/contacts')
def contacts():
    """Contacts management page."""
    session = get_session()

    # Get all contacts with companies
    contacts = session.query(Contact, Company).join(
        Company, Contact.company_id == Company.company_id
    ).order_by(Contact.company_id, Contact.role).all()

    contact_list = []
    for contact, company in contacts:
        contact_list.append({
            'contact_id': contact.contact_id,
            'name': contact.name,
            'role': contact.role,
            'email': contact.email,
            'linkedin_url': contact.linkedin_url,
            'company_name': company.name,
            'company_id': company.company_id,
            'notes': contact.notes,
            'created_at': contact.created_at.strftime('%Y-%m-%d') if contact.created_at else 'Unknown'
        })

    # Group by company
    contacts_by_company = {}
    for c in contact_list:
        company_name = c['company_name']
        if company_name not in contacts_by_company:
            contacts_by_company[company_name] = []
        contacts_by_company[company_name].append(c)

    return render_template('contacts.html', contacts_by_company=contacts_by_company)


@app.route('/api/contact/add', methods=['POST'])
def add_contact():
    """Add a new contact."""
    session = get_session()

    data = request.json
    contact = Contact(
        company_id=data['company_id'],
        name=data['name'],
        role=data['role'],
        email=data.get('email'),
        linkedin_url=data.get('linkedin_url'),
        notes=data.get('notes')
    )
    session.add(contact)
    session.commit()

    return jsonify({'success': True, 'message': 'Contact added successfully'})


@app.route('/outreach/<job_pk>')
def outreach_view(job_pk):
    """View outreach pack for a job."""
    session = get_session()

    job = session.query(JobPosting).filter_by(job_pk=job_pk).first()
    if not job:
        return "Job not found", 404

    company = session.query(Company).filter_by(company_id=job.company_id).first()
    prep = session.query(PrepArtifact).filter_by(job_pk=job_pk).first()

    if not prep:
        return redirect(url_for('job_detail', job_pk=job_pk))

    # Parse outreach pack from prep artifact
    fit_mapping = json.loads(prep.fit_mapping_json or '{}')
    company_dossier = json.loads(prep.company_dossier_json or '{}')

    # Get or generate outreach pack
    from src.enrichment import LLMWorkflows
    outreach_pack = LLMWorkflows.workflow_outreach_pack(
        job.title,
        company.name,
        job.apply_url,
        company_dossier,
        fit_mapping.get('positioning_angle', ''),
        job_pk
    )

    # Get contacts for this company
    contacts = session.query(Contact).filter_by(company_id=company.company_id).all()

    # Get outreach history
    outreach_history = session.query(OutreachSequence, Contact).join(
        Contact, OutreachSequence.contact_id == Contact.contact_id
    ).filter(OutreachSequence.job_pk == job_pk).order_by(
        OutreachSequence.created_at.desc()
    ).all()

    history_list = []
    for seq, contact in outreach_history:
        history_list.append({
            'sequence_id': seq.sequence_id,
            'contact_name': contact.name,
            'channel': seq.channel,
            'sent_at': seq.sent_at.strftime('%Y-%m-%d %H:%M') if seq.sent_at else 'Scheduled',
            'reply_outcome': seq.reply_outcome,
            'message_body': seq.message_body
        })

    outreach_data = {
        'job_pk': job_pk,
        'job_title': job.title,
        'company_name': company.name,
        'company_id': company.company_id,
        'outreach_pack': outreach_pack,
        'contacts': [{'contact_id': c.contact_id, 'name': c.name, 'role': c.role} for c in contacts],
        'history': history_list
    }

    return render_template('outreach.html', data=outreach_data)


@app.route('/api/outreach/send', methods=['POST'])
def send_outreach():
    """Log an outreach message (manual send)."""
    session = get_session()

    data = request.json
    outreach = OutreachSequence(
        job_pk=data['job_pk'],
        contact_id=data['contact_id'],
        channel=data['channel'],
        message_subject=data.get('message_subject'),
        message_body=data['message_body'],
        sent_at=datetime.utcnow(),
        reply_outcome='no_reply'
    )
    session.add(outreach)
    session.commit()

    return jsonify({'success': True, 'message': 'Outreach logged successfully'})


@app.route('/interviews')
def interviews():
    """Interviews page."""
    session = get_session()

    # Get all interviews with applications and jobs
    from src.db.models import Interview
    interviews = session.query(Interview, Application, JobPosting, Company).join(
        Application, Interview.application_id == Application.application_id
    ).join(
        JobPosting, Application.job_pk == JobPosting.job_pk
    ).join(
        Company, JobPosting.company_id == Company.company_id
    ).order_by(Interview.scheduled_at.desc()).all()

    interview_list = []
    for interview, app, job, company in interviews:
        interview_list.append({
            'interview_id': interview.interview_id,
            'job_title': job.title,
            'company_name': company.name,
            'round_type': interview.round_type,
            'scheduled_at': interview.scheduled_at.strftime('%Y-%m-%d %H:%M') if interview.scheduled_at else 'TBD',
            'interviewer_names': interview.interviewer_names,
            'outcome': interview.outcome,
            'notes': interview.notes,
            'job_pk': job.job_pk
        })

    # Separate upcoming and past
    now = datetime.utcnow()
    upcoming = [i for i in interview_list if i['scheduled_at'] != 'TBD' and
                datetime.strptime(i['scheduled_at'], '%Y-%m-%d %H:%M') >= now]
    past = [i for i in interview_list if i['scheduled_at'] != 'TBD' and
            datetime.strptime(i['scheduled_at'], '%Y-%m-%d %H:%M') < now]

    return render_template('interviews.html', upcoming=upcoming, past=past)


@app.route('/settings')
def settings():
    """Settings page."""
    return render_template('settings.html', env=os.environ)


@app.route('/api/settings/update', methods=['POST'])
def update_settings():
    """Update settings (writes to .env file)."""
    data = request.json

    # Read current .env
    env_path = '.env'
    lines = []
    if os.path.exists(env_path):
        with open(env_path, 'r') as f:
            lines = f.readlines()

    # Update or add settings
    settings_to_update = {
        'TARGET_SALARY_MIN': data.get('salary_min'),
        'ALLOWED_ROLE_FAMILIES': data.get('role_families'),
    }

    updated_lines = []
    for line in lines:
        key = line.split('=')[0] if '=' in line else ''
        if key in settings_to_update:
            updated_lines.append(f"{key}={settings_to_update[key]}\n")
            del settings_to_update[key]
        else:
            updated_lines.append(line)

    # Add new settings
    for key, value in settings_to_update.items():
        if value:
            updated_lines.append(f"{key}={value}\n")

    # Write back
    with open(env_path, 'w') as f:
        f.writelines(updated_lines)

    return jsonify({'success': True, 'message': 'Settings updated'})


@app.route('/analytics')
def analytics():
    """Analytics and insights page."""
    session = get_session()

    # Gather analytics
    analytics_data = {
        'total_companies': session.query(Company).count(),
        'total_jobs': session.query(JobPosting).count(),
        'eligible_jobs': session.query(JobPosting).filter_by(is_eligible_location=True).count(),
        'scored_jobs': session.query(JobScore).count(),
        'applications': session.query(Application).count(),
        'interviews': session.query(Application).filter(
            Application.status.in_(['screen', 'tech_screen', 'onsite', 'final'])
        ).count(),
        'offers': session.query(Application).filter_by(status='offer').count(),

        # Conversion funnel
        'shortlisted': session.query(JobPosting).filter_by(status='shortlisted').count(),
        'outreach_sent': session.query(Application).filter_by(status='outreach_sent').count(),
        'applied': session.query(Application).filter(
            Application.status.in_(['applied', 'screen', 'tech_screen', 'onsite', 'final', 'offer'])
        ).count(),

        # Score distribution
        'score_85_plus': session.query(JobScore).filter(JobScore.total_score >= 85).count(),
        'score_75_84': session.query(JobScore).filter(
            JobScore.total_score >= 75, JobScore.total_score < 85
        ).count(),
        'score_70_74': session.query(JobScore).filter(
            JobScore.total_score >= 70, JobScore.total_score < 75
        ).count(),

        # By role family
        'by_role_family': {},

        # By location
        'remote_jobs': session.query(JobPosting).filter_by(is_remote=True, is_eligible_location=True).count(),
        'chicago_jobs': session.query(JobPosting).filter_by(is_chicago=True).count(),
    }

    # Role family breakdown
    from sqlalchemy import func
    role_counts = session.query(
        JobPosting.role_family,
        func.count(JobPosting.job_pk)
    ).filter(
        JobPosting.is_eligible_location == True
    ).group_by(JobPosting.role_family).all()

    analytics_data['by_role_family'] = {role: count for role, count in role_counts}

    return render_template('analytics.html', data=analytics_data)


@app.route('/search')
def search():
    """Search across all jobs."""
    query = request.args.get('q', '')
    session = get_session()

    if not query:
        return render_template('search.html', jobs=[], query='')

    # Search in title, company name, and description
    results = session.query(JobPosting, Company, JobScore).join(
        Company, JobPosting.company_id == Company.company_id
    ).outerjoin(
        JobScore, JobPosting.job_pk == JobScore.job_pk
    ).filter(
        (JobPosting.title.contains(query)) |
        (Company.name.contains(query)) |
        (JobPosting.description_text.contains(query))
    ).limit(50).all()

    jobs = []
    for job, company, score in results:
        jobs.append({
            'job_pk': job.job_pk,
            'title': job.title,
            'company_name': company.name,
            'location_raw': job.location_raw,
            'is_remote': job.is_remote,
            'is_chicago': job.is_chicago,
            'score': score.total_score if score else None,
            'apply_url': job.apply_url
        })

    return render_template('search.html', jobs=jobs, query=query)


if __name__ == '__main__':
    # Initialize database if needed
    init_db()

    # Run app
    app.run(host='127.0.0.1', port=5001, debug=True)
