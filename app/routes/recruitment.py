from flask import Blueprint, render_template, request, flash, redirect, url_for
from flask_login import login_required, current_user
from app import db
from app.models.recruitment import JobPosting, Application
from datetime import datetime, date
from sqlalchemy import func

bp = Blueprint('recruitment', __name__)

@bp.route('/')
@login_required
def index():
    return redirect(url_for('recruitment.job_postings'))

@bp.route('/jobs')
@login_required
def job_postings():
    page = request.args.get('page', 1, type=int)
    status = request.args.get('status', 'active')
    department = request.args.get('department')
    
    query = JobPosting.query
    
    if status:
        query = query.filter(JobPosting.status == status)
    
    if department:
        query = query.filter(JobPosting.department == department)
    
    jobs = query.order_by(JobPosting.created_at.desc()).paginate(
        page=page, per_page=10, error_out=False
    )
    
    # Get departments for filter
    departments = db.session.query(JobPosting.department).distinct().all()
    departments = [dept[0] for dept in departments if dept[0]]
    
    return render_template('recruitment/job_postings.html',
                         jobs=jobs,
                         departments=departments,
                         selected_status=status,
                         selected_department=department)

@bp.route('/jobs/view/<int:id>')
@login_required
def view_job(id):
    job = JobPosting.query.get_or_404(id)
    return render_template('recruitment/view_job.html', job=job)

@bp.route('/jobs/add', methods=['GET', 'POST'])
@login_required
def add_job():
    if not (current_user.has_permission('recruitment') or current_user.has_permission('all')):
        flash('Bạn không có quyền tạo tin tuyển dụng.', 'error')
        return redirect(url_for('recruitment.job_postings'))
    
    if request.method == 'POST':
        try:
            job = JobPosting(
                title=request.form.get('title'),
                department=request.form.get('department'),
                location=request.form.get('location'),
                employment_type=request.form.get('employment_type'),
                description=request.form.get('description'),
                requirements=request.form.get('requirements'),
                responsibilities=request.form.get('responsibilities'),
                benefits=request.form.get('benefits'),
                salary_min=float(request.form.get('salary_min')) if request.form.get('salary_min') else None,
                salary_max=float(request.form.get('salary_max')) if request.form.get('salary_max') else None,
                application_deadline=datetime.strptime(request.form.get('application_deadline'), '%Y-%m-%d').date() if request.form.get('application_deadline') else None,
                start_date=datetime.strptime(request.form.get('start_date'), '%Y-%m-%d').date() if request.form.get('start_date') else None,
                positions_available=int(request.form.get('positions_available', 1)),
                contact_person=request.form.get('contact_person'),
                contact_email=request.form.get('contact_email'),
                contact_phone=request.form.get('contact_phone'),
                created_by=current_user.id
            )
            
            db.session.add(job)
            db.session.commit()
            
            flash('Tin tuyển dụng đã được tạo thành công!', 'success')
            return redirect(url_for('recruitment.view_job', id=job.id))
            
        except Exception as e:
            db.session.rollback()
            flash(f'Có lỗi xảy ra: {str(e)}', 'error')
    
    return render_template('recruitment/add_job.html')

@bp.route('/jobs/edit/<int:id>', methods=['GET', 'POST'])
@login_required
def edit_job(id):
    if not (current_user.has_permission('recruitment') or current_user.has_permission('all')):
        flash('Bạn không có quyền chỉnh sửa tin tuyển dụng.', 'error')
        return redirect(url_for('recruitment.view_job', id=id))
    
    job = JobPosting.query.get_or_404(id)
    
    if request.method == 'POST':
        try:
            job.title = request.form.get('title')
            job.department = request.form.get('department')
            job.location = request.form.get('location')
            job.employment_type = request.form.get('employment_type')
            job.description = request.form.get('description')
            job.requirements = request.form.get('requirements')
            job.responsibilities = request.form.get('responsibilities')
            job.benefits = request.form.get('benefits')
            job.salary_min = float(request.form.get('salary_min')) if request.form.get('salary_min') else None
            job.salary_max = float(request.form.get('salary_max')) if request.form.get('salary_max') else None
            job.application_deadline = datetime.strptime(request.form.get('application_deadline'), '%Y-%m-%d').date() if request.form.get('application_deadline') else None
            job.start_date = datetime.strptime(request.form.get('start_date'), '%Y-%m-%d').date() if request.form.get('start_date') else None
            job.positions_available = int(request.form.get('positions_available', 1))
            job.contact_person = request.form.get('contact_person')
            job.contact_email = request.form.get('contact_email')
            job.contact_phone = request.form.get('contact_phone')
            job.status = request.form.get('status')
            
            db.session.commit()
            flash('Tin tuyển dụng đã được cập nhật!', 'success')
            return redirect(url_for('recruitment.view_job', id=id))
            
        except Exception as e:
            db.session.rollback()
            flash(f'Có lỗi xảy ra: {str(e)}', 'error')
    
    return render_template('recruitment/edit_job.html', job=job)

@bp.route('/applications')
@login_required
def applications():
    if not (current_user.has_permission('recruitment') or current_user.has_permission('all')):
        flash('Bạn không có quyền xem đơn ứng tuyển.', 'error')
        return redirect(url_for('recruitment.job_postings'))
    
    page = request.args.get('page', 1, type=int)
    job_id = request.args.get('job_id', type=int)
    status = request.args.get('status')
    
    query = Application.query.join(JobPosting)
    
    if job_id:
        query = query.filter(Application.job_posting_id == job_id)
    
    if status:
        query = query.filter(Application.status == status)
    
    applications = query.order_by(Application.created_at.desc()).paginate(
        page=page, per_page=20, error_out=False
    )
    
    jobs = JobPosting.query.order_by(JobPosting.title).all()
    status_choices = Application.get_status_choices()
    
    return render_template('recruitment/applications.html',
                         applications=applications,
                         jobs=jobs,
                         status_choices=status_choices,
                         selected_job=job_id,
                         selected_status=status)

@bp.route('/applications/view/<int:id>')
@login_required
def view_application(id):
    if not (current_user.has_permission('recruitment') or current_user.has_permission('all')):
        flash('Bạn không có quyền xem đơn ứng tuyển.', 'error')
        return redirect(url_for('recruitment.applications'))
    
    application = Application.query.get_or_404(id)
    return render_template('recruitment/view_application.html', application=application)

@bp.route('/applications/schedule-interview/<int:id>', methods=['POST'])
@login_required
def schedule_interview(id):
    if not (current_user.has_permission('recruitment') or current_user.has_permission('all')):
        flash('Bạn không có quyền lên lịch phỏng vấn.', 'error')
        return redirect(url_for('recruitment.view_application', id=id))
    
    application = Application.query.get_or_404(id)
    
    try:
        interview_date = datetime.strptime(
            f"{request.form.get('interview_date')} {request.form.get('interview_time')}", 
            '%Y-%m-%d %H:%M'
        )
        location = request.form.get('interview_location')
        interviewer_id = int(request.form.get('interviewer_id'))
        
        application.schedule_interview(interview_date, location, interviewer_id)
        db.session.commit()
        
        flash('Lịch phỏng vấn đã được tạo!', 'success')
    except Exception as e:
        db.session.rollback()
        flash(f'Có lỗi xảy ra: {str(e)}', 'error')
    
    return redirect(url_for('recruitment.view_application', id=id))

@bp.route('/applications/evaluate/<int:id>', methods=['POST'])
@login_required
def evaluate_application(id):
    if not (current_user.has_permission('recruitment') or current_user.has_permission('all')):
        flash('Bạn không có quyền đánh giá ứng viên.', 'error')
        return redirect(url_for('recruitment.view_application', id=id))
    
    application = Application.query.get_or_404(id)
    
    try:
        application.technical_score = int(request.form.get('technical_score')) if request.form.get('technical_score') else None
        application.communication_score = int(request.form.get('communication_score')) if request.form.get('communication_score') else None
        application.cultural_fit_score = int(request.form.get('cultural_fit_score')) if request.form.get('cultural_fit_score') else None
        application.evaluation_notes = request.form.get('evaluation_notes')
        
        application.calculate_overall_score()
        db.session.commit()
        
        flash('Đánh giá ứng viên đã được lưu!', 'success')
    except Exception as e:
        db.session.rollback()
        flash(f'Có lỗi xảy ra: {str(e)}', 'error')
    
    return redirect(url_for('recruitment.view_application', id=id))

@bp.route('/applications/make-offer/<int:id>', methods=['POST'])
@login_required
def make_offer(id):
    if not (current_user.has_permission('recruitment') or current_user.has_permission('all')):
        flash('Bạn không có quyền gửi offer.', 'error')
        return redirect(url_for('recruitment.view_application', id=id))
    
    application = Application.query.get_or_404(id)
    
    try:
        offer_details = {
            'salary': float(request.form.get('offer_salary')),
            'start_date': request.form.get('offer_start_date'),
            'benefits': request.form.get('offer_benefits'),
            'notes': request.form.get('offer_notes')
        }
        
        application.make_offer(offer_details, current_user.id)
        db.session.commit()
        
        flash('Offer đã được gửi!', 'success')
    except Exception as e:
        db.session.rollback()
        flash(f'Có lỗi xảy ra: {str(e)}', 'error')
    
    return redirect(url_for('recruitment.view_application', id=id))

@bp.route('/applications/hire/<int:id>', methods=['POST'])
@login_required
def hire_applicant(id):
    if not (current_user.has_permission('recruitment') or current_user.has_permission('all')):
        flash('Bạn không có quyền tuyển dụng.', 'error')
        return redirect(url_for('recruitment.view_application', id=id))
    
    application = Application.query.get_or_404(id)
    
    try:
        application.hire(current_user.id)
        db.session.commit()
        
        flash('Ứng viên đã được tuyển dụng!', 'success')
    except Exception as e:
        db.session.rollback()
        flash(f'Có lỗi xảy ra: {str(e)}', 'error')
    
    return redirect(url_for('recruitment.view_application', id=id))

@bp.route('/applications/reject/<int:id>', methods=['POST'])
@login_required
def reject_application(id):
    if not (current_user.has_permission('recruitment') or current_user.has_permission('all')):
        flash('Bạn không có quyền từ chối ứng viên.', 'error')
        return redirect(url_for('recruitment.view_application', id=id))
    
    application = Application.query.get_or_404(id)
    
    try:
        reason = request.form.get('rejection_reason')
        application.reject(reason, current_user.id)
        db.session.commit()
        
        flash('Đã từ chối ứng viên.', 'info')
    except Exception as e:
        db.session.rollback()
        flash(f'Có lỗi xảy ra: {str(e)}', 'error')
    
    return redirect(url_for('recruitment.view_application', id=id))

@bp.route('/report')
@login_required
def report():
    if not (current_user.has_permission('recruitment') or current_user.has_permission('all')):
        flash('Bạn không có quyền xem báo cáo tuyển dụng.', 'error')
        return redirect(url_for('recruitment.job_postings'))
    
    # Job postings statistics
    total_jobs = JobPosting.query.count()
    active_jobs = JobPosting.query.filter_by(status='active').count()
    
    # Applications statistics
    total_applications = Application.query.count()
    pending_applications = Application.query.filter_by(status='pending').count()
    hired_applications = Application.query.filter_by(status='hired').count()
    
    # Applications by status
    status_summary = db.session.query(
        Application.status,
        func.count(Application.id).label('count')
    ).group_by(Application.status).all()
    
    # Applications by job
    job_summary = db.session.query(
        JobPosting.title,
        JobPosting.department,
        func.count(Application.id).label('application_count')
    ).join(Application).group_by(JobPosting.id, JobPosting.title, JobPosting.department).all()
    
    return render_template('recruitment/report.html',
                         total_jobs=total_jobs,
                         active_jobs=active_jobs,
                         total_applications=total_applications,
                         pending_applications=pending_applications,
                         hired_applications=hired_applications,
                         status_summary=status_summary,
                         job_summary=job_summary)