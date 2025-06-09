from flask import Blueprint, render_template, request, flash, redirect, url_for, jsonify
from flask_login import login_required, current_user
from app import db
from app.models.employee import Employee
from app.models.payroll import Payroll
from datetime import datetime, date, timedelta
from calendar import monthrange
from sqlalchemy import func

bp = Blueprint('payroll', __name__)

@bp.route('/')
@login_required
def index():
    if current_user.has_permission('payroll') or current_user.has_permission('all'):
        return redirect(url_for('payroll.all_payrolls'))
    else:
        return redirect(url_for('payroll.my_payroll'))

@bp.route('/my')
@login_required
def my_payroll():
    if not current_user.employee:
        flash('Bạn chưa có hồ sơ nhân viên.', 'error')
        return redirect(url_for('main.dashboard'))
    
    employee = current_user.employee
    
    page = request.args.get('page', 1, type=int)
    year = request.args.get('year', date.today().year, type=int)
    
    payrolls = Payroll.query.filter(
        Payroll.employee_id == employee.id,
        db.extract('year', Payroll.pay_period_start) == year
    ).order_by(Payroll.pay_period_end.desc()).paginate(
        page=page, per_page=12, error_out=False
    )
    
    # Calculate yearly totals
    yearly_totals = db.session.query(
        func.sum(Payroll.gross_pay).label('total_gross'),
        func.sum(Payroll.net_pay).label('total_net'),
        func.sum(Payroll.total_deductions).label('total_deductions'),
        func.sum(Payroll.overtime_pay).label('total_overtime')
    ).filter(
        Payroll.employee_id == employee.id,
        db.extract('year', Payroll.pay_period_start) == year
    ).first()
    
    return render_template('payroll/my_payroll.html', 
                         payrolls=payrolls,
                         yearly_totals=yearly_totals,
                         selected_year=year,
                         employee=employee)

@bp.route('/all')
@login_required
def all_payrolls():
    if not (current_user.has_permission('payroll') or current_user.has_permission('all')):
        flash('Bạn không có quyền xem tất cả bảng lương.', 'error')
        return redirect(url_for('payroll.my_payroll'))
    
    page = request.args.get('page', 1, type=int)
    employee_id = request.args.get('employee_id', type=int)
    month = request.args.get('month', type=int)
    year = request.args.get('year', date.today().year, type=int)
    status = request.args.get('status')
    
    query = Payroll.query.join(Employee)
    
    if employee_id:
        query = query.filter(Payroll.employee_id == employee_id)
    
    if month:
        query = query.filter(db.extract('month', Payroll.pay_period_start) == month)
    
    if year:
        query = query.filter(db.extract('year', Payroll.pay_period_start) == year)
    
    if status:
        query = query.filter(Payroll.status == status)
    
    payrolls = query.order_by(Payroll.pay_period_end.desc()).paginate(
        page=page, per_page=20, error_out=False
    )
    
    employees = Employee.query.filter_by(status='active').order_by(Employee.full_name).all()
    
    return render_template('payroll/all_payrolls.html',
                         payrolls=payrolls,
                         employees=employees,
                         selected_employee=employee_id,
                         selected_month=month,
                         selected_year=year,
                         selected_status=status)

@bp.route('/view/<int:id>')
@login_required
def view(id):
    payroll = Payroll.query.get_or_404(id)
    
    # Check permissions
    if not (current_user.has_permission('payroll') or 
            current_user.has_permission('all') or
            (current_user.employee and current_user.employee.id == payroll.employee_id)):
        flash('Bạn không có quyền xem bảng lương này.', 'error')
        return redirect(url_for('main.dashboard'))
    
    return render_template('payroll/view.html', payroll=payroll)

@bp.route('/generate', methods=['GET', 'POST'])
@login_required
def generate():
    if not (current_user.has_permission('payroll') or current_user.has_permission('all')):
        flash('Bạn không có quyền tạo bảng lương.', 'error')
        return redirect(url_for('payroll.all_payrolls'))
    
    if request.method == 'POST':
        try:
            employee_ids = request.form.getlist('employee_ids')
            month = int(request.form.get('month'))
            year = int(request.form.get('year'))
            
            if not employee_ids:
                flash('Vui lòng chọn ít nhất một nhân viên.', 'error')
                return render_template('payroll/generate.html')
            
            # Calculate pay period
            _, last_day = monthrange(year, month)
            pay_period_start = date(year, month, 1)
            pay_period_end = date(year, month, last_day)
            
            generated_count = 0
            
            for employee_id in employee_ids:
                employee = Employee.query.get(employee_id)
                if not employee:
                    continue
                
                # Check if payroll already exists for this period
                existing = Payroll.query.filter(
                    Payroll.employee_id == employee_id,
                    Payroll.pay_period_start == pay_period_start,
                    Payroll.pay_period_end == pay_period_end
                ).first()
                
                if existing:
                    continue
                
                # Generate payroll
                payroll = Payroll.generate_payroll_for_employee(
                    employee, pay_period_start, pay_period_end
                )
                
                db.session.add(payroll)
                generated_count += 1
            
            db.session.commit()
            flash(f'Đã tạo {generated_count} bảng lương thành công!', 'success')
            return redirect(url_for('payroll.all_payrolls'))
            
        except Exception as e:
            db.session.rollback()
            flash(f'Có lỗi xảy ra: {str(e)}', 'error')
    
    employees = Employee.query.filter_by(status='active').order_by(Employee.full_name).all()
    return render_template('payroll/generate.html', employees=employees)

@bp.route('/edit/<int:id>', methods=['GET', 'POST'])
@login_required
def edit(id):
    if not (current_user.has_permission('payroll') or current_user.has_permission('all')):
        flash('Bạn không có quyền chỉnh sửa bảng lương.', 'error')
        return redirect(url_for('payroll.view', id=id))
    
    payroll = Payroll.query.get_or_404(id)
    
    if payroll.status == 'paid':
        flash('Không thể chỉnh sửa bảng lương đã thanh toán.', 'error')
        return redirect(url_for('payroll.view', id=id))
    
    if request.method == 'POST':
        try:
            # Update payroll details
            payroll.basic_salary = float(request.form.get('basic_salary', 0))
            payroll.housing_allowance = float(request.form.get('housing_allowance', 0))
            payroll.transport_allowance = float(request.form.get('transport_allowance', 0))
            payroll.meal_allowance = float(request.form.get('meal_allowance', 0))
            payroll.other_allowances = float(request.form.get('other_allowances', 0))
            
            payroll.overtime_hours = float(request.form.get('overtime_hours', 0))
            payroll.overtime_rate = float(request.form.get('overtime_rate', 0))
            payroll.calculate_overtime_pay()
            
            payroll.performance_bonus = float(request.form.get('performance_bonus', 0))
            payroll.holiday_bonus = float(request.form.get('holiday_bonus', 0))
            payroll.other_bonuses = float(request.form.get('other_bonuses', 0))
            
            payroll.tax_deduction = float(request.form.get('tax_deduction', 0))
            payroll.insurance_deduction = float(request.form.get('insurance_deduction', 0))
            payroll.loan_deduction = float(request.form.get('loan_deduction', 0))
            payroll.other_deductions = float(request.form.get('other_deductions', 0))
            
            payroll.notes = request.form.get('notes')
            
            # Recalculate totals
            payroll.calculate_totals()
            
            db.session.commit()
            flash('Bảng lương đã được cập nhật!', 'success')
            return redirect(url_for('payroll.view', id=id))
            
        except Exception as e:
            db.session.rollback()
            flash(f'Có lỗi xảy ra: {str(e)}', 'error')
    
    return render_template('payroll/edit.html', payroll=payroll)

@bp.route('/approve/<int:id>', methods=['POST'])
@login_required
def approve(id):
    if not (current_user.has_permission('payroll') or current_user.has_permission('all')):
        flash('Bạn không có quyền duyệt bảng lương.', 'error')
        return redirect(url_for('payroll.view', id=id))
    
    payroll = Payroll.query.get_or_404(id)
    
    if payroll.status != 'draft':
        flash('Chỉ có thể duyệt bảng lương ở trạng thái nháp.', 'error')
        return redirect(url_for('payroll.view', id=id))
    
    payroll.status = 'approved'
    payroll.approved_by = current_user.id
    payroll.approved_at = datetime.utcnow()
    
    try:
        db.session.commit()
        flash('Bảng lương đã được duyệt!', 'success')
    except Exception as e:
        db.session.rollback()
        flash(f'Có lỗi xảy ra: {str(e)}', 'error')
    
    return redirect(url_for('payroll.view', id=id))

@bp.route('/mark-paid/<int:id>', methods=['POST'])
@login_required
def mark_paid(id):
    if not (current_user.has_permission('payroll') or current_user.has_permission('all')):
        flash('Bạn không có quyền đánh dấu thanh toán.', 'error')
        return redirect(url_for('payroll.view', id=id))
    
    payroll = Payroll.query.get_or_404(id)
    
    if payroll.status != 'approved':
        flash('Chỉ có thể thanh toán bảng lương đã được duyệt.', 'error')
        return redirect(url_for('payroll.view', id=id))
    
    payroll.status = 'paid'
    
    try:
        db.session.commit()
        flash('Đã đánh dấu bảng lương là đã thanh toán!', 'success')
    except Exception as e:
        db.session.rollback()
        flash(f'Có lỗi xảy ra: {str(e)}', 'error')
    
    return redirect(url_for('payroll.view', id=id))

@bp.route('/report')
@login_required
def report():
    if not (current_user.has_permission('payroll') or current_user.has_permission('all')):
        flash('Bạn không có quyền xem báo cáo lương.', 'error')
        return redirect(url_for('payroll.my_payroll'))
    
    year = request.args.get('year', date.today().year, type=int)
    month = request.args.get('month', type=int)
    
    query = db.session.query(
        Employee.department,
        func.count(Payroll.id).label('employee_count'),
        func.sum(Payroll.gross_pay).label('total_gross'),
        func.sum(Payroll.net_pay).label('total_net'),
        func.sum(Payroll.total_deductions).label('total_deductions')
    ).join(Employee).filter(
        db.extract('year', Payroll.pay_period_start) == year
    )
    
    if month:
        query = query.filter(db.extract('month', Payroll.pay_period_start) == month)
    
    department_summary = query.group_by(Employee.department).all()
    
    # Overall totals
    total_query = db.session.query(
        func.sum(Payroll.gross_pay).label('total_gross'),
        func.sum(Payroll.net_pay).label('total_net'),
        func.sum(Payroll.total_deductions).label('total_deductions'),
        func.count(Payroll.id).label('total_payrolls')
    ).filter(
        db.extract('year', Payroll.pay_period_start) == year
    )
    
    if month:
        total_query = total_query.filter(db.extract('month', Payroll.pay_period_start) == month)
    
    totals = total_query.first()
    
    return render_template('payroll/report.html',
                         department_summary=department_summary,
                         totals=totals,
                         selected_year=year,
                         selected_month=month)