from flask import Blueprint, render_template, request, flash, redirect, url_for, jsonify
from flask_login import login_required, current_user
from app import db
from app.models.employee import Employee
from app.models.user import User
from datetime import datetime, date
import os
from werkzeug.utils import secure_filename

bp = Blueprint('employee', __name__)

def allowed_file(filename):
    ALLOWED_EXTENSIONS = {'txt', 'pdf', 'png', 'jpg', 'jpeg', 'gif', 'doc', 'docx'}
    return '.' in filename and filename.rsplit('.', 1)[1].lower() in ALLOWED_EXTENSIONS

@bp.route('/')
@login_required
def list_employees():
    if not (current_user.has_permission('employee_management') or current_user.has_permission('all')):
        flash('Bạn không có quyền truy cập trang này.', 'error')
        return redirect(url_for('main.dashboard'))
    
    page = request.args.get('page', 1, type=int)
    search = request.args.get('search', '')
    department = request.args.get('department', '')
    status = request.args.get('status', 'active')
    
    query = Employee.query
    
    if search:
        query = query.filter(
            Employee.full_name.ilike(f'%{search}%') |
            Employee.employee_id.ilike(f'%{search}%') |
            Employee.position.ilike(f'%{search}%')
        )
    
    if department:
        query = query.filter(Employee.department == department)
    
    if status:
        query = query.filter(Employee.status == status)
    
    employees = query.order_by(Employee.full_name).paginate(
        page=page, per_page=20, error_out=False
    )
    
    # Get departments for filter
    departments = db.session.query(Employee.department).distinct().all()
    departments = [dept[0] for dept in departments if dept[0]]
    
    return render_template('employee/list.html', 
                         employees=employees, 
                         departments=departments,
                         search=search,
                         selected_department=department,
                         selected_status=status)

@bp.route('/view/<int:id>')
@login_required
def view(id):
    employee = Employee.query.get_or_404(id)
    
    # Check permissions
    if not (current_user.has_permission('employee_management') or 
            current_user.has_permission('all') or
            (current_user.employee and current_user.employee.id == id)):
        flash('Bạn không có quyền xem thông tin này.', 'error')
        return redirect(url_for('main.dashboard'))
    
    return render_template('employee/view.html', employee=employee)

@bp.route('/add', methods=['GET', 'POST'])
@login_required
def add():
    if not (current_user.has_permission('employee_management') or current_user.has_permission('all')):
        flash('Bạn không có quyền thêm nhân viên.', 'error')
        return redirect(url_for('employee.list_employees'))
    
    if request.method == 'POST':
        try:
            # Create user account first
            username = request.form.get('username')
            email = request.form.get('email')
            password = request.form.get('password', 'password123')  # Default password
            role = request.form.get('role', 'employee')
            
            # Check if username/email already exists
            if User.query.filter_by(username=username).first():
                flash('Tên đăng nhập đã tồn tại.', 'error')
                return render_template('employee/add.html')
            
            if User.query.filter_by(email=email).first():
                flash('Email đã được sử dụng.', 'error')
                return render_template('employee/add.html')
            
            user = User(username=username, email=email, role=role)
            user.set_password(password)
            db.session.add(user)
            db.session.flush()  # Get user ID
            
            # Create employee record
            employee = Employee(
                user_id=user.id,
                employee_id=request.form.get('employee_id'),
                first_name=request.form.get('first_name'),
                last_name=request.form.get('last_name'),
                full_name=f"{request.form.get('first_name')} {request.form.get('last_name')}",
                date_of_birth=datetime.strptime(request.form.get('date_of_birth'), '%Y-%m-%d').date() if request.form.get('date_of_birth') else None,
                gender=request.form.get('gender'),
                phone=request.form.get('phone'),
                address=request.form.get('address'),
                emergency_contact=request.form.get('emergency_contact'),
                emergency_phone=request.form.get('emergency_phone'),
                department=request.form.get('department'),
                position=request.form.get('position'),
                hire_date=datetime.strptime(request.form.get('hire_date'), '%Y-%m-%d').date() if request.form.get('hire_date') else date.today(),
                employment_type=request.form.get('employment_type', 'full_time'),
                salary=float(request.form.get('salary')) if request.form.get('salary') else None,
                manager_id=int(request.form.get('manager_id')) if request.form.get('manager_id') else None
            )
            
            db.session.add(employee)
            db.session.commit()
            
            flash(f'Nhân viên {employee.full_name} đã được thêm thành công!', 'success')
            return redirect(url_for('employee.view', id=employee.id))
            
        except Exception as e:
            db.session.rollback()
            flash(f'Có lỗi xảy ra: {str(e)}', 'error')
            return render_template('employee/add.html')
    
    # Get managers for dropdown
    managers = Employee.query.filter(
        Employee.position.ilike('%manager%') | 
        Employee.position.ilike('%leader%') |
        Employee.position.ilike('%supervisor%')
    ).all()
    
    return render_template('employee/add.html', managers=managers)

@bp.route('/edit/<int:id>', methods=['GET', 'POST'])
@login_required
def edit(id):
    employee = Employee.query.get_or_404(id)
    
    if not (current_user.has_permission('employee_management') or current_user.has_permission('all')):
        flash('Bạn không có quyền chỉnh sửa thông tin nhân viên.', 'error')
        return redirect(url_for('employee.view', id=id))
    
    if request.method == 'POST':
        try:
            # Update employee information
            employee.first_name = request.form.get('first_name')
            employee.last_name = request.form.get('last_name')
            employee.full_name = f"{employee.first_name} {employee.last_name}"
            employee.date_of_birth = datetime.strptime(request.form.get('date_of_birth'), '%Y-%m-%d').date() if request.form.get('date_of_birth') else None
            employee.gender = request.form.get('gender')
            employee.phone = request.form.get('phone')
            employee.address = request.form.get('address')
            employee.emergency_contact = request.form.get('emergency_contact')
            employee.emergency_phone = request.form.get('emergency_phone')
            employee.department = request.form.get('department')
            employee.position = request.form.get('position')
            employee.employment_type = request.form.get('employment_type')
            employee.salary = float(request.form.get('salary')) if request.form.get('salary') else None
            employee.manager_id = int(request.form.get('manager_id')) if request.form.get('manager_id') else None
            employee.status = request.form.get('status')
            
            if request.form.get('termination_date'):
                employee.termination_date = datetime.strptime(request.form.get('termination_date'), '%Y-%m-%d').date()
            
            # Update user role if changed
            if request.form.get('role') and employee.user:
                employee.user.role = request.form.get('role')
            
            db.session.commit()
            flash('Thông tin nhân viên đã được cập nhật!', 'success')
            return redirect(url_for('employee.view', id=id))
            
        except Exception as e:
            db.session.rollback()
            flash(f'Có lỗi xảy ra: {str(e)}', 'error')
    
    # Get managers for dropdown
    managers = Employee.query.filter(
        Employee.id != id,  # Exclude current employee
        (Employee.position.ilike('%manager%') | 
         Employee.position.ilike('%leader%') |
         Employee.position.ilike('%supervisor%'))
    ).all()
    
    return render_template('employee/edit.html', employee=employee, managers=managers)

@bp.route('/delete/<int:id>', methods=['POST'])
@login_required
def delete(id):
    if not current_user.has_permission('all'):
        flash('Bạn không có quyền xóa nhân viên.', 'error')
        return redirect(url_for('employee.view', id=id))
    
    employee = Employee.query.get_or_404(id)
    
    try:
        # Instead of deleting, mark as terminated
        employee.status = 'terminated'
        employee.termination_date = date.today()
        
        # Deactivate user account
        if employee.user:
            employee.user.is_active = False
        
        db.session.commit()
        flash(f'Nhân viên {employee.full_name} đã được đánh dấu là đã nghỉ việc.', 'success')
        
    except Exception as e:
        db.session.rollback()
        flash(f'Có lỗi xảy ra: {str(e)}', 'error')
    
    return redirect(url_for('employee.list_employees'))

@bp.route('/upload-avatar/<int:id>', methods=['POST'])
@login_required
def upload_avatar(id):
    employee = Employee.query.get_or_404(id)
    
    # Check permissions
    if not (current_user.has_permission('employee_management') or 
            current_user.has_permission('all') or
            (current_user.employee and current_user.employee.id == id)):
        flash('Bạn không có quyền cập nhật ảnh đại diện.', 'error')
        return redirect(url_for('employee.view', id=id))
    
    if 'avatar' not in request.files:
        flash('Không có file nào được chọn.', 'error')
        return redirect(url_for('employee.view', id=id))
    
    file = request.files['avatar']
    if file.filename == '':
        flash('Không có file nào được chọn.', 'error')
        return redirect(url_for('employee.view', id=id))
    
    if file and allowed_file(file.filename):
        filename = secure_filename(f"avatar_{employee.id}_{file.filename}")
        upload_folder = os.path.join('app', 'static', 'uploads', 'avatars')
        os.makedirs(upload_folder, exist_ok=True)
        file_path = os.path.join(upload_folder, filename)
        file.save(file_path)
        
        # Update employee avatar path
        employee.avatar = f"uploads/avatars/{filename}"
        db.session.commit()
        
        flash('Ảnh đại diện đã được cập nhật!', 'success')
    else:
        flash('Định dạng file không được hỗ trợ.', 'error')
    
    return redirect(url_for('employee.view', id=id))