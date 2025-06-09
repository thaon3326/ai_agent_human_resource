from flask import Blueprint, render_template, request, flash, redirect, url_for, jsonify
from flask_login import login_required, current_user
from app import db
from app.models.user import User
from app.models.employee import Employee
from app.models.attendance import Attendance
from app.models.payroll import Payroll
from app.models.benefit import Benefit
from app.models.reward import Reward
from app.models.recruitment import JobPosting, Application
from datetime import datetime, date, timedelta
from sqlalchemy import func

bp = Blueprint('main', __name__)

@bp.route('/')
def index():
    if current_user.is_authenticated:
        return redirect(url_for('main.dashboard'))
    return redirect(url_for('auth.login'))

@bp.route('/dashboard')
@login_required
def dashboard():
    # Get dashboard statistics based on user role
    stats = {}
    
    if current_user.has_permission('all') or current_user.has_role('hr'):
        # Admin/HR dashboard
        stats = {
            'total_employees': Employee.query.filter_by(status='active').count(),
            'total_departments': db.session.query(Employee.department).distinct().count(),
            'pending_applications': Application.query.filter_by(status='pending').count(),
            'active_job_postings': JobPosting.query.filter_by(status='active').count(),
            'pending_rewards': Reward.query.filter_by(status='pending').count(),
            'this_month_hires': Employee.query.filter(
                Employee.hire_date >= date.today().replace(day=1)
            ).count()
        }
        
        # Recent activities
        recent_employees = Employee.query.order_by(Employee.created_at.desc()).limit(5).all()
        recent_applications = Application.query.order_by(Application.created_at.desc()).limit(5).all()
        pending_rewards = Reward.query.filter_by(status='pending').order_by(Reward.created_at.desc()).limit(5).all()
        
        return render_template('dashboard/admin.html', 
                             stats=stats, 
                             recent_employees=recent_employees,
                             recent_applications=recent_applications,
                             pending_rewards=pending_rewards)
    
    elif current_user.has_role('leader'):
        # Leader dashboard
        if current_user.employee:
            subordinates = current_user.employee.subordinates
            stats = {
                'team_size': len(subordinates),
                'team_attendance_today': sum(1 for emp in subordinates 
                                           if Attendance.query.filter_by(
                                               employee_id=emp.id, 
                                               date=date.today()
                                           ).first()),
                'pending_team_rewards': Reward.query.join(Employee).filter(
                    Employee.manager_id == current_user.employee.id,
                    Reward.status == 'pending'
                ).count()
            }
            
            return render_template('dashboard/leader.html', 
                                 stats=stats, 
                                 subordinates=subordinates)
    
    else:
        # Employee dashboard
        if current_user.employee:
            employee = current_user.employee
            
            # Get current month attendance
            current_month_attendance = employee.get_current_month_attendance()
            
            # Get latest payroll
            latest_payroll = Payroll.query.filter_by(employee_id=employee.id).order_by(
                Payroll.pay_period_end.desc()
            ).first()
            
            # Get active benefits
            active_benefits = Benefit.query.filter_by(
                employee_id=employee.id, 
                status='active'
            ).all()
            
            # Get recent rewards
            recent_rewards = Reward.query.filter_by(employee_id=employee.id).order_by(
                Reward.created_at.desc()
            ).limit(5).all()
            
            stats = {
                'days_worked_this_month': len(current_month_attendance),
                'total_benefits': len(active_benefits),
                'total_rewards': Reward.query.filter_by(employee_id=employee.id).count(),
                'years_of_service': employee.years_of_service
            }
            
            return render_template('dashboard/employee.html',
                                 employee=employee,
                                 stats=stats,
                                 current_month_attendance=current_month_attendance,
                                 latest_payroll=latest_payroll,
                                 active_benefits=active_benefits,
                                 recent_rewards=recent_rewards)
    
    return render_template('dashboard/default.html')

@bp.route('/profile')
@login_required
def profile():
    return render_template('profile.html', user=current_user)

@bp.route('/search')
@login_required
def search():
    query = request.args.get('q', '')
    if not query:
        return jsonify({'results': []})
    
    results = []
    
    # Search employees (if user has permission)
    if current_user.has_permission('employee_management') or current_user.has_permission('all'):
        employees = Employee.query.filter(
            Employee.full_name.ilike(f'%{query}%') |
            Employee.employee_id.ilike(f'%{query}%') |
            Employee.department.ilike(f'%{query}%') |
            Employee.position.ilike(f'%{query}%')
        ).limit(10).all()
        
        for emp in employees:
            results.append({
                'type': 'employee',
                'id': emp.id,
                'title': emp.full_name,
                'subtitle': f'{emp.position} - {emp.department}',
                'url': url_for('employee.view', id=emp.id)
            })
    
    return jsonify({'results': results})

@bp.route('/notifications')
@login_required
def notifications():
    notifications = []
    
    if current_user.has_permission('all') or current_user.has_role('hr'):
        # Pending applications
        pending_apps = Application.query.filter_by(status='pending').count()
        if pending_apps > 0:
            notifications.append({
                'type': 'info',
                'message': f'Có {pending_apps} đơn ứng tuyển chờ xử lý',
                'url': url_for('recruitment.applications')
            })
        
        # Pending rewards
        pending_rewards = Reward.query.filter_by(status='pending').count()
        if pending_rewards > 0:
            notifications.append({
                'type': 'info',
                'message': f'Có {pending_rewards} đề xuất khen thưởng chờ duyệt',
                'url': url_for('admin.pending_rewards')
            })
    
    return jsonify({'notifications': notifications})