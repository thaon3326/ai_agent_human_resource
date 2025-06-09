from flask import Blueprint, render_template, request, flash, redirect, url_for
from flask_login import login_required, current_user
from app import db
from app.models.user import User
from app.models.employee import Employee
from app.models.reward import Reward
from datetime import datetime, date
from sqlalchemy import func

bp = Blueprint('admin', __name__)

@bp.route('/')
@login_required
def index():
    if not current_user.has_permission('all'):
        flash('Bạn không có quyền truy cập trang quản trị.', 'error')
        return redirect(url_for('main.dashboard'))
    
    return render_template('admin/index.html')

@bp.route('/users')
@login_required
def users():
    if not current_user.has_permission('all'):
        flash('Bạn không có quyền quản lý người dùng.', 'error')
        return redirect(url_for('main.dashboard'))
    
    page = request.args.get('page', 1, type=int)
    search = request.args.get('search', '')
    role = request.args.get('role', '')
    status = request.args.get('status', '')
    
    query = User.query
    
    if search:
        query = query.filter(
            User.username.ilike(f'%{search}%') |
            User.email.ilike(f'%{search}%')
        )
    
    if role:
        query = query.filter(User.role == role)
    
    if status == 'active':
        query = query.filter(User.is_active == True)
    elif status == 'inactive':
        query = query.filter(User.is_active == False)
    
    users = query.order_by(User.created_at.desc()).paginate(
        page=page, per_page=20, error_out=False
    )
    
    return render_template('admin/users.html',
                         users=users,
                         search=search,
                         selected_role=role,
                         selected_status=status)

@bp.route('/users/toggle-status/<int:id>', methods=['POST'])
@login_required
def toggle_user_status(id):
    if not current_user.has_permission('all'):
        flash('Bạn không có quyền thay đổi trạng thái người dùng.', 'error')
        return redirect(url_for('admin.users'))
    
    user = User.query.get_or_404(id)
    
    if user.id == current_user.id:
        flash('Bạn không thể vô hiệu hóa tài khoản của chính mình.', 'error')
        return redirect(url_for('admin.users'))
    
    user.is_active = not user.is_active
    
    try:
        db.session.commit()
        status = 'kích hoạt' if user.is_active else 'vô hiệu hóa'
        flash(f'Đã {status} tài khoản {user.username}.', 'success')
    except Exception as e:
        db.session.rollback()
        flash(f'Có lỗi xảy ra: {str(e)}', 'error')
    
    return redirect(url_for('admin.users'))

@bp.route('/users/change-role/<int:id>', methods=['POST'])
@login_required
def change_user_role(id):
    if not current_user.has_permission('all'):
        flash('Bạn không có quyền thay đổi vai trò người dùng.', 'error')
        return redirect(url_for('admin.users'))
    
    user = User.query.get_or_404(id)
    new_role = request.form.get('role')
    
    if new_role not in ['admin', 'hr', 'leader', 'employee']:
        flash('Vai trò không hợp lệ.', 'error')
        return redirect(url_for('admin.users'))
    
    user.role = new_role
    
    try:
        db.session.commit()
        flash(f'Đã thay đổi vai trò của {user.username} thành {new_role}.', 'success')
    except Exception as e:
        db.session.rollback()
        flash(f'Có lỗi xảy ra: {str(e)}', 'error')
    
    return redirect(url_for('admin.users'))

@bp.route('/rewards')
@login_required
def rewards():
    if not (current_user.has_permission('all') or current_user.has_role('hr')):
        flash('Bạn không có quyền quản lý khen thưởng.', 'error')
        return redirect(url_for('main.dashboard'))
    
    page = request.args.get('page', 1, type=int)
    status = request.args.get('status', 'pending')
    employee_id = request.args.get('employee_id', type=int)
    
    query = Reward.query.join(Employee)
    
    if status:
        query = query.filter(Reward.status == status)
    
    if employee_id:
        query = query.filter(Reward.employee_id == employee_id)
    
    rewards = query.order_by(Reward.created_at.desc()).paginate(
        page=page, per_page=20, error_out=False
    )
    
    employees = Employee.query.filter_by(status='active').order_by(Employee.full_name).all()
    
    return render_template('admin/rewards.html',
                         rewards=rewards,
                         employees=employees,
                         selected_status=status,
                         selected_employee=employee_id)

@bp.route('/rewards/add', methods=['GET', 'POST'])
@login_required
def add_reward():
    if not (current_user.has_permission('all') or current_user.has_role('hr')):
        flash('Bạn không có quyền thêm khen thưởng.', 'error')
        return redirect(url_for('admin.rewards'))
    
    if request.method == 'POST':
        try:
            reward = Reward(
                employee_id=int(request.form.get('employee_id')),
                reward_type=request.form.get('reward_type'),
                title=request.form.get('title'),
                description=request.form.get('description'),
                reason=request.form.get('reason'),
                monetary_value=float(request.form.get('monetary_value', 0)),
                award_date=datetime.strptime(request.form.get('award_date'), '%Y-%m-%d').date(),
                effective_date=datetime.strptime(request.form.get('effective_date'), '%Y-%m-%d').date() if request.form.get('effective_date') else None,
                public_recognition=bool(request.form.get('public_recognition')),
                nominated_by=current_user.id
            )
            
            db.session.add(reward)
            db.session.commit()
            
            flash('Khen thưởng đã được thêm thành công!', 'success')
            return redirect(url_for('admin.view_reward', id=reward.id))
            
        except Exception as e:
            db.session.rollback()
            flash(f'Có lỗi xảy ra: {str(e)}', 'error')
    
    employees = Employee.query.filter_by(status='active').order_by(Employee.full_name).all()
    reward_types = Reward.get_reward_types()
    
    return render_template('admin/add_reward.html',
                         employees=employees,
                         reward_types=reward_types)

@bp.route('/rewards/view/<int:id>')
@login_required
def view_reward(id):
    if not (current_user.has_permission('all') or current_user.has_role('hr')):
        flash('Bạn không có quyền xem khen thưởng.', 'error')
        return redirect(url_for('main.dashboard'))
    
    reward = Reward.query.get_or_404(id)
    return render_template('admin/view_reward.html', reward=reward)

@bp.route('/rewards/approve/<int:id>', methods=['POST'])
@login_required
def approve_reward(id):
    if not (current_user.has_permission('all') or current_user.has_role('hr')):
        flash('Bạn không có quyền duyệt khen thưởng.', 'error')
        return redirect(url_for('admin.view_reward', id=id))
    
    reward = Reward.query.get_or_404(id)
    
    if not reward.is_pending:
        flash('Chỉ có thể duyệt khen thưởng đang chờ xử lý.', 'error')
        return redirect(url_for('admin.view_reward', id=id))
    
    reward.approve(current_user.id)
    
    try:
        db.session.commit()
        flash('Khen thưởng đã được duyệt!', 'success')
    except Exception as e:
        db.session.rollback()
        flash(f'Có lỗi xảy ra: {str(e)}', 'error')
    
    return redirect(url_for('admin.view_reward', id=id))

@bp.route('/rewards/reject/<int:id>', methods=['POST'])
@login_required
def reject_reward(id):
    if not (current_user.has_permission('all') or current_user.has_role('hr')):
        flash('Bạn không có quyền từ chối khen thưởng.', 'error')
        return redirect(url_for('admin.view_reward', id=id))
    
    reward = Reward.query.get_or_404(id)
    
    if not reward.is_pending:
        flash('Chỉ có thể từ chối khen thưởng đang chờ xử lý.', 'error')
        return redirect(url_for('admin.view_reward', id=id))
    
    reason = request.form.get('rejection_reason')
    if not reason:
        flash('Vui lòng nhập lý do từ chối.', 'error')
        return redirect(url_for('admin.view_reward', id=id))
    
    reward.reject(current_user.id, reason)
    
    try:
        db.session.commit()
        flash('Đã từ chối khen thưởng.', 'info')
    except Exception as e:
        db.session.rollback()
        flash(f'Có lỗi xảy ra: {str(e)}', 'error')
    
    return redirect(url_for('admin.view_reward', id=id))

@bp.route('/pending-rewards')
@login_required
def pending_rewards():
    if not (current_user.has_permission('all') or current_user.has_role('hr')):
        flash('Bạn không có quyền xem khen thưởng chờ duyệt.', 'error')
        return redirect(url_for('main.dashboard'))
    
    rewards = Reward.query.filter_by(status='pending').join(Employee).order_by(Reward.created_at.desc()).all()
    
    return render_template('admin/pending_rewards.html', rewards=rewards)

@bp.route('/system-stats')
@login_required
def system_stats():
    if not current_user.has_permission('all'):
        flash('Bạn không có quyền xem thống kê hệ thống.', 'error')
        return redirect(url_for('main.dashboard'))
    
    # User statistics
    total_users = User.query.count()
    active_users = User.query.filter_by(is_active=True).count()
    users_by_role = db.session.query(
        User.role,
        func.count(User.id).label('count')
    ).group_by(User.role).all()
    
    # Employee statistics
    total_employees = Employee.query.count()
    active_employees = Employee.query.filter_by(status='active').count()
    employees_by_department = db.session.query(
        Employee.department,
        func.count(Employee.id).label('count')
    ).group_by(Employee.department).all()
    
    # Recent activities
    recent_users = User.query.order_by(User.created_at.desc()).limit(5).all()
    recent_employees = Employee.query.order_by(Employee.created_at.desc()).limit(5).all()
    
    return render_template('admin/system_stats.html',
                         total_users=total_users,
                         active_users=active_users,
                         users_by_role=users_by_role,
                         total_employees=total_employees,
                         active_employees=active_employees,
                         employees_by_department=employees_by_department,
                         recent_users=recent_users,
                         recent_employees=recent_employees)