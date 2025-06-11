from flask import Blueprint, render_template, request, flash, redirect, url_for, jsonify
from flask_login import login_required, current_user
from app import db
from app.models.employee import Employee
from app.models.attendance import Attendance
from datetime import datetime, date, time, timedelta
from sqlalchemy import func, extract

bp = Blueprint('attendance', __name__)

@bp.route('/')
@login_required
def index():
    if current_user.has_permission('all') or current_user.has_role('hr'):
        return redirect(url_for('attendance.list_attendance'))
    else:
        return redirect(url_for('attendance.my_attendance'))

@bp.route('/list')
@login_required
def list_attendance():
    if not current_user.has_permission('hr'):
        flash('Bạn không có quyền truy cập trang này', 'error')
        return redirect(url_for('attendance.my_attendance'))
    
    page = request.args.get('page', 1, type=int)
    employee_search = request.args.get('employee_search', '')
    date_from = request.args.get('date_from', '')
    date_to = request.args.get('date_to', '')
    department = request.args.get('department', '')
    
    query = Attendance.query.join(Employee)
    
    # Apply filters
    if employee_search:
        query = query.filter(
            Employee.full_name.contains(employee_search) |
            Employee.employee_id.contains(employee_search)
        )
    
    if date_from:
        query = query.filter(Attendance.date >= datetime.strptime(date_from, '%Y-%m-%d').date())
    
    if date_to:
        query = query.filter(Attendance.date <= datetime.strptime(date_to, '%Y-%m-%d').date())
    
    if department:
        query = query.filter(Employee.department == department)
    
    attendances = query.order_by(Attendance.date.desc()).paginate(
        page=page, per_page=20, error_out=False
    )
    
    # Get statistics
    stats_query = query
    total_records = stats_query.count()
    avg_hours = stats_query.with_entities(func.avg(Attendance.total_hours)).scalar() or 0
    total_overtime = stats_query.with_entities(func.sum(Attendance.overtime_hours)).scalar() or 0
    late_count = stats_query.filter(Attendance.is_late == True).count()
    
    stats = {
        'total_records': total_records,
        'avg_hours': avg_hours,
        'total_overtime': total_overtime,
        'late_count': late_count
    }
    
    # Get departments for filter
    departments = db.session.query(Employee.department).filter(
        Employee.department.isnot(None)
    ).distinct().all()
    departments = [dept[0] for dept in departments]
    
    return render_template('attendance/list.html',
                         attendances=attendances,
                         stats=stats,
                         employee_search=employee_search,
                         date_from=date_from,
                         date_to=date_to,
                         selected_department=department,
                         departments=departments)

@bp.route('/my')
@login_required
def my_attendance():
    if not current_user.employee:
        flash('Bạn chưa có hồ sơ nhân viên.', 'error')
        return redirect(url_for('main.dashboard'))
    
    employee = current_user.employee
    
    # Get current month attendance
    today = date.today()
    start_of_month = today.replace(day=1)
    
    attendances = Attendance.query.filter(
        Attendance.employee_id == employee.id,
        Attendance.date >= start_of_month,
        Attendance.date <= today
    ).order_by(Attendance.date.desc()).all()
    
    # Calculate statistics
    total_days = len(attendances)
    present_days = len([att for att in attendances if att.status == 'present'])
    late_days = len([att for att in attendances if att.is_late])
    total_hours = sum(att.total_hours or 0 for att in attendances)
    overtime_hours = sum(att.overtime_hours or 0 for att in attendances)
    
    stats = {
        'total_days': total_days,
        'present_days': present_days,
        'absent_days': total_days - present_days,
        'late_days': late_days,
        'total_hours': round(total_hours, 2),
        'overtime_hours': round(overtime_hours, 2)
    }
    
    return render_template('attendance/my_attendance.html', 
                         attendances=attendances, 
                         stats=stats,
                         employee=employee)

@bp.route('/all')
@login_required
def all_attendance():
    if not (current_user.has_permission('all') or current_user.has_role('hr') or current_user.has_role('leader')):
        flash('Bạn không có quyền xem tất cả chấm công.', 'error')
        return redirect(url_for('attendance.my_attendance'))
    
    page = request.args.get('page', 1, type=int)
    employee_id = request.args.get('employee_id', type=int)
    date_from = request.args.get('date_from')
    date_to = request.args.get('date_to')
    status = request.args.get('status')
    
    query = Attendance.query.join(Employee)
    
    # Filter by employee if specified
    if employee_id:
        query = query.filter(Attendance.employee_id == employee_id)
    elif current_user.has_role('leader') and current_user.employee:
        # Leaders can only see their team's attendance
        subordinate_ids = [emp.id for emp in current_user.employee.subordinates]
        subordinate_ids.append(current_user.employee.id)  # Include self
        query = query.filter(Attendance.employee_id.in_(subordinate_ids))
    
    # Filter by date range
    if date_from:
        query = query.filter(Attendance.date >= datetime.strptime(date_from, '%Y-%m-%d').date())
    if date_to:
        query = query.filter(Attendance.date <= datetime.strptime(date_to, '%Y-%m-%d').date())
    
    # Filter by status
    if status:
        query = query.filter(Attendance.status == status)
    
    attendances = query.order_by(Attendance.date.desc()).paginate(
        page=page, per_page=20, error_out=False
    )
    
    # Get employees for filter
    if current_user.has_role('leader') and current_user.employee:
        employees = [current_user.employee] + current_user.employee.subordinates
    else:
        employees = Employee.query.filter_by(status='active').order_by(Employee.full_name).all()
    
    return render_template('attendance/all_attendance.html', 
                         attendances=attendances,
                         employees=employees,
                         selected_employee=employee_id,
                         date_from=date_from,
                         date_to=date_to,
                         selected_status=status)

@bp.route('/check-in', methods=['POST'])
@login_required
def check_in():
    if not current_user.employee:
        return jsonify({'success': False, 'message': 'Bạn chưa có hồ sơ nhân viên.'})
    
    employee = current_user.employee
    today = date.today()
    
    # Check if already checked in today
    existing_attendance = Attendance.query.filter_by(
        employee_id=employee.id,
        date=today
    ).first()
    
    if existing_attendance and existing_attendance.check_in:
        return jsonify({'success': False, 'message': 'Bạn đã check-in hôm nay rồi.'})
    
    current_time = datetime.now().time()
    
    if existing_attendance:
        # Update existing record
        existing_attendance.check_in = current_time
        existing_attendance.status = 'present'
    else:
        # Create new attendance record
        attendance = Attendance(
            employee_id=employee.id,
            date=today,
            check_in=current_time,
            status='present'
        )
        db.session.add(attendance)
    
    try:
        db.session.commit()
        return jsonify({
            'success': True, 
            'message': f'Check-in thành công lúc {current_time.strftime("%H:%M")}',
            'time': current_time.strftime("%H:%M")
        })
    except Exception as e:
        db.session.rollback()
        return jsonify({'success': False, 'message': 'Có lỗi xảy ra khi check-in.'})

@bp.route('/check-out', methods=['POST'])
@login_required
def check_out():
    if not current_user.employee:
        return jsonify({'success': False, 'message': 'Bạn chưa có hồ sơ nhân viên.'})
    
    employee = current_user.employee
    today = date.today()
    
    attendance = Attendance.query.filter_by(
        employee_id=employee.id,
        date=today
    ).first()
    
    if not attendance or not attendance.check_in:
        return jsonify({'success': False, 'message': 'Bạn chưa check-in hôm nay.'})
    
    if attendance.check_out:
        return jsonify({'success': False, 'message': 'Bạn đã check-out hôm nay rồi.'})
    
    current_time = datetime.now().time()
    attendance.check_out = current_time
    attendance.calculate_hours()
    
    try:
        db.session.commit()
        return jsonify({
            'success': True, 
            'message': f'Check-out thành công lúc {current_time.strftime("%H:%M")}',
            'time': current_time.strftime("%H:%M"),
            'total_hours': attendance.total_hours
        })
    except Exception as e:
        db.session.rollback()
        return jsonify({'success': False, 'message': 'Có lỗi xảy ra khi check-out.'})

@bp.route('/break-start', methods=['POST'])
@login_required
def break_start():
    if not current_user.employee:
        return jsonify({'success': False, 'message': 'Bạn chưa có hồ sơ nhân viên.'})
    
    employee = current_user.employee
    today = date.today()
    
    attendance = Attendance.query.filter_by(
        employee_id=employee.id,
        date=today
    ).first()
    
    if not attendance or not attendance.check_in:
        return jsonify({'success': False, 'message': 'Bạn chưa check-in hôm nay.'})
    
    if attendance.break_start:
        return jsonify({'success': False, 'message': 'Bạn đã bắt đầu nghỉ giải lao rồi.'})
    
    current_time = datetime.now().time()
    attendance.break_start = current_time
    
    try:
        db.session.commit()
        return jsonify({
            'success': True, 
            'message': f'Bắt đầu nghỉ giải lao lúc {current_time.strftime("%H:%M")}',
            'time': current_time.strftime("%H:%M")
        })
    except Exception as e:
        db.session.rollback()
        return jsonify({'success': False, 'message': 'Có lỗi xảy ra.'})

@bp.route('/break-end', methods=['POST'])
@login_required
def break_end():
    if not current_user.employee:
        return jsonify({'success': False, 'message': 'Bạn chưa có hồ sơ nhân viên.'})
    
    employee = current_user.employee
    today = date.today()
    
    attendance = Attendance.query.filter_by(
        employee_id=employee.id,
        date=today
    ).first()
    
    if not attendance or not attendance.break_start:
        return jsonify({'success': False, 'message': 'Bạn chưa bắt đầu nghỉ giải lao.'})
    
    if attendance.break_end:
        return jsonify({'success': False, 'message': 'Bạn đã kết thúc nghỉ giải lao rồi.'})
    
    current_time = datetime.now().time()
    attendance.break_end = current_time
    attendance.calculate_hours()
    
    try:
        db.session.commit()
        return jsonify({
            'success': True, 
            'message': f'Kết thúc nghỉ giải lao lúc {current_time.strftime("%H:%M")}',
            'time': current_time.strftime("%H:%M")
        })
    except Exception as e:
        db.session.rollback()
        return jsonify({'success': False, 'message': 'Có lỗi xảy ra.'})

@bp.route('/status/<int:id>')
@login_required
def status(id):
    if not current_user.employee or current_user.employee.id != id:
        if not (current_user.has_permission('all') or current_user.has_role('hr')):
            return jsonify({'success': False, 'message': 'Không có quyền truy cập.'})
    
    today = date.today()
    attendance = Attendance.query.filter_by(
        employee_id=id,
        date=today
    ).first()
    
    if not attendance:
        return jsonify({
            'checked_in': False,
            'checked_out': False,
            'on_break': False
        })
    
    return jsonify({
        'checked_in': bool(attendance.check_in),
        'checked_out': bool(attendance.check_out),
        'on_break': bool(attendance.break_start and not attendance.break_end),
        'check_in_time': attendance.check_in.strftime("%H:%M") if attendance.check_in else None,
        'check_out_time': attendance.check_out.strftime("%H:%M") if attendance.check_out else None,
        'total_hours': attendance.total_hours
    })

@bp.route('/report')
@login_required
def report():
    if not (current_user.has_permission('all') or current_user.has_role('hr') or current_user.has_role('leader')):
        flash('Bạn không có quyền xem báo cáo chấm công.', 'error')
        return redirect(url_for('attendance.my_attendance'))
    
    # Get monthly attendance summary
    current_month = date.today().month
    current_year = date.today().year
    
    query = db.session.query(
        Employee.id,
        Employee.full_name,
        Employee.department,
        func.count(Attendance.id).label('total_days'),
        func.sum(Attendance.total_hours).label('total_hours'),
        func.sum(Attendance.overtime_hours).label('overtime_hours')
    ).join(Attendance).filter(
        extract('month', Attendance.date) == current_month,
        extract('year', Attendance.date) == current_year
    ).group_by(Employee.id, Employee.full_name, Employee.department)
    
    if current_user.has_role('leader') and current_user.employee:
        subordinate_ids = [emp.id for emp in current_user.employee.subordinates]
        subordinate_ids.append(current_user.employee.id)
        query = query.filter(Employee.id.in_(subordinate_ids))
    
    attendance_summary = query.all()
    
    return render_template('attendance/report.html', 
                         attendance_summary=attendance_summary,
                         current_month=current_month,
                         current_year=current_year)