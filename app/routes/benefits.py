from flask import Blueprint, render_template, request, flash, redirect, url_for
from flask_login import login_required, current_user
from app import db
from app.models.employee import Employee
from app.models.benefit import Benefit
from datetime import datetime, date
from sqlalchemy import func

bp = Blueprint('benefits', __name__)

@bp.route('/')
@login_required
def index():
    if current_user.has_permission('benefits') or current_user.has_permission('all'):
        return redirect(url_for('benefits.all_benefits'))
    else:
        return redirect(url_for('benefits.my_benefits'))

@bp.route('/my')
@login_required
def my_benefits():
    if not current_user.employee:
        flash('Bạn chưa có hồ sơ nhân viên.', 'error')
        return redirect(url_for('main.dashboard'))
    
    employee = current_user.employee
    
    # Get active benefits
    active_benefits = Benefit.query.filter_by(
        employee_id=employee.id,
        status='active'
    ).order_by(Benefit.start_date.desc()).all()
    
    # Get expired/inactive benefits
    inactive_benefits = Benefit.query.filter(
        Benefit.employee_id == employee.id,
        Benefit.status != 'active'
    ).order_by(Benefit.end_date.desc()).all()
    
    # Calculate total benefit value
    total_value = sum(benefit.total_value or 0 for benefit in active_benefits)
    
    return render_template('benefits/my_benefits.html',
                         active_benefits=active_benefits,
                         inactive_benefits=inactive_benefits,
                         total_value=total_value,
                         employee=employee)

@bp.route('/all')
@login_required
def all_benefits():
    if not (current_user.has_permission('benefits') or current_user.has_permission('all')):
        flash('Bạn không có quyền xem tất cả phúc lợi.', 'error')
        return redirect(url_for('benefits.my_benefits'))
    
    page = request.args.get('page', 1, type=int)
    employee_id = request.args.get('employee_id', type=int)
    benefit_type = request.args.get('benefit_type')
    status = request.args.get('status')
    
    query = Benefit.query.join(Employee)
    
    if employee_id:
        query = query.filter(Benefit.employee_id == employee_id)
    
    if benefit_type:
        query = query.filter(Benefit.benefit_type == benefit_type)
    
    if status:
        query = query.filter(Benefit.status == status)
    
    benefits = query.order_by(Benefit.created_at.desc()).paginate(
        page=page, per_page=20, error_out=False
    )
    
    employees = Employee.query.filter_by(status='active').order_by(Employee.full_name).all()
    benefit_types = Benefit.get_benefit_types()
    
    return render_template('benefits/all_benefits.html',
                         benefits=benefits,
                         employees=employees,
                         benefit_types=benefit_types,
                         selected_employee=employee_id,
                         selected_type=benefit_type,
                         selected_status=status)

@bp.route('/view/<int:id>')
@login_required
def view(id):
    benefit = Benefit.query.get_or_404(id)
    
    # Check permissions
    if not (current_user.has_permission('benefits') or 
            current_user.has_permission('all') or
            (current_user.employee and current_user.employee.id == benefit.employee_id)):
        flash('Bạn không có quyền xem phúc lợi này.', 'error')
        return redirect(url_for('main.dashboard'))
    
    return render_template('benefits/view.html', benefit=benefit)

@bp.route('/add', methods=['GET', 'POST'])
@login_required
def add():
    if not (current_user.has_permission('benefits') or current_user.has_permission('all')):
        flash('Bạn không có quyền thêm phúc lợi.', 'error')
        return redirect(url_for('benefits.all_benefits'))
    
    if request.method == 'POST':
        try:
            benefit = Benefit(
                employee_id=int(request.form.get('employee_id')),
                benefit_type=request.form.get('benefit_type'),
                benefit_name=request.form.get('benefit_name'),
                description=request.form.get('description'),
                employer_contribution=float(request.form.get('employer_contribution', 0)),
                employee_contribution=float(request.form.get('employee_contribution', 0)),
                start_date=datetime.strptime(request.form.get('start_date'), '%Y-%m-%d').date(),
                end_date=datetime.strptime(request.form.get('end_date'), '%Y-%m-%d').date() if request.form.get('end_date') else None,
                provider_name=request.form.get('provider_name'),
                provider_contact=request.form.get('provider_contact'),
                policy_number=request.form.get('policy_number'),
                status=request.form.get('status', 'active')
            )
            
            benefit.calculate_total_value()
            
            db.session.add(benefit)
            db.session.commit()
            
            flash('Phúc lợi đã được thêm thành công!', 'success')
            return redirect(url_for('benefits.view', id=benefit.id))
            
        except Exception as e:
            db.session.rollback()
            flash(f'Có lỗi xảy ra: {str(e)}', 'error')
    
    employees = Employee.query.filter_by(status='active').order_by(Employee.full_name).all()
    benefit_types = Benefit.get_benefit_types()
    
    return render_template('benefits/add.html', 
                         employees=employees, 
                         benefit_types=benefit_types)

@bp.route('/edit/<int:id>', methods=['GET', 'POST'])
@login_required
def edit(id):
    if not (current_user.has_permission('benefits') or current_user.has_permission('all')):
        flash('Bạn không có quyền chỉnh sửa phúc lợi.', 'error')
        return redirect(url_for('benefits.view', id=id))
    
    benefit = Benefit.query.get_or_404(id)
    
    if request.method == 'POST':
        try:
            benefit.benefit_type = request.form.get('benefit_type')
            benefit.benefit_name = request.form.get('benefit_name')
            benefit.description = request.form.get('description')
            benefit.employer_contribution = float(request.form.get('employer_contribution', 0))
            benefit.employee_contribution = float(request.form.get('employee_contribution', 0))
            benefit.start_date = datetime.strptime(request.form.get('start_date'), '%Y-%m-%d').date()
            benefit.end_date = datetime.strptime(request.form.get('end_date'), '%Y-%m-%d').date() if request.form.get('end_date') else None
            benefit.provider_name = request.form.get('provider_name')
            benefit.provider_contact = request.form.get('provider_contact')
            benefit.policy_number = request.form.get('policy_number')
            benefit.status = request.form.get('status')
            
            benefit.calculate_total_value()
            
            db.session.commit()
            flash('Phúc lợi đã được cập nhật!', 'success')
            return redirect(url_for('benefits.view', id=id))
            
        except Exception as e:
            db.session.rollback()
            flash(f'Có lỗi xảy ra: {str(e)}', 'error')
    
    benefit_types = Benefit.get_benefit_types()
    return render_template('benefits/edit.html', benefit=benefit, benefit_types=benefit_types)

@bp.route('/delete/<int:id>', methods=['POST'])
@login_required
def delete(id):
    if not current_user.has_permission('all'):
        flash('Bạn không có quyền xóa phúc lợi.', 'error')
        return redirect(url_for('benefits.view', id=id))
    
    benefit = Benefit.query.get_or_404(id)
    
    try:
        db.session.delete(benefit)
        db.session.commit()
        flash('Phúc lợi đã được xóa.', 'success')
        return redirect(url_for('benefits.all_benefits'))
    except Exception as e:
        db.session.rollback()
        flash(f'Có lỗi xảy ra: {str(e)}', 'error')
        return redirect(url_for('benefits.view', id=id))

@bp.route('/approve/<int:id>', methods=['POST'])
@login_required
def approve(id):
    if not (current_user.has_permission('benefits') or current_user.has_permission('all')):
        flash('Bạn không có quyền duyệt phúc lợi.', 'error')
        return redirect(url_for('benefits.view', id=id))
    
    benefit = Benefit.query.get_or_404(id)
    
    benefit.status = 'active'
    benefit.approved_by = current_user.id
    benefit.approved_at = datetime.utcnow()
    
    try:
        db.session.commit()
        flash('Phúc lợi đã được duyệt!', 'success')
    except Exception as e:
        db.session.rollback()
        flash(f'Có lỗi xảy ra: {str(e)}', 'error')
    
    return redirect(url_for('benefits.view', id=id))

@bp.route('/report')
@login_required
def report():
    if not (current_user.has_permission('benefits') or current_user.has_permission('all')):
        flash('Bạn không có quyền xem báo cáo phúc lợi.', 'error')
        return redirect(url_for('benefits.my_benefits'))
    
    # Benefits by type
    benefit_summary = db.session.query(
        Benefit.benefit_type,
        func.count(Benefit.id).label('count'),
        func.sum(Benefit.total_value).label('total_value')
    ).filter_by(status='active').group_by(Benefit.benefit_type).all()
    
    # Benefits by department
    department_summary = db.session.query(
        Employee.department,
        func.count(Benefit.id).label('benefit_count'),
        func.sum(Benefit.total_value).label('total_value')
    ).join(Employee).filter(Benefit.status == 'active').group_by(Employee.department).all()
    
    # Overall statistics
    total_benefits = Benefit.query.filter_by(status='active').count()
    total_value = db.session.query(func.sum(Benefit.total_value)).filter_by(status='active').scalar() or 0
    
    return render_template('benefits/report.html',
                         benefit_summary=benefit_summary,
                         department_summary=department_summary,
                         total_benefits=total_benefits,
                         total_value=total_value)