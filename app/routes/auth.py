from flask import Blueprint, render_template, request, flash, redirect, url_for
from flask_login import login_user, logout_user, login_required, current_user
from werkzeug.urls import url_parse
from app import db
from app.models.user import User
from datetime import datetime

bp = Blueprint('auth', __name__)

@bp.route('/login', methods=['GET', 'POST'])
def login():
    if current_user.is_authenticated:
        return redirect(url_for('main.dashboard'))
    
    if request.method == 'POST':
        username = request.form.get('username')
        password = request.form.get('password')
        remember_me = bool(request.form.get('remember_me'))
        
        if not username or not password:
            flash('Vui lòng nhập đầy đủ thông tin đăng nhập.', 'error')
            return render_template('auth/login.html')
        
        user = User.query.filter_by(username=username).first()
        
        if user is None or not user.check_password(password):
            flash('Tên đăng nhập hoặc mật khẩu không đúng.', 'error')
            return render_template('auth/login.html')
        
        if not user.is_active:
            flash('Tài khoản của bạn đã bị vô hiệu hóa.', 'error')
            return render_template('auth/login.html')
        
        # Update last login
        user.last_login = datetime.utcnow()
        db.session.commit()
        
        login_user(user, remember=remember_me)
        
        next_page = request.args.get('next')
        if not next_page or url_parse(next_page).netloc != '':
            next_page = url_for('main.dashboard')
        
        flash(f'Chào mừng {user.username}!', 'success')
        return redirect(next_page)
    
    return render_template('auth/login.html')

@bp.route('/logout')
@login_required
def logout():
    logout_user()
    flash('Bạn đã đăng xuất thành công.', 'info')
    return redirect(url_for('auth.login'))

@bp.route('/register', methods=['GET', 'POST'])
def register():
    if current_user.is_authenticated:
        return redirect(url_for('main.dashboard'))
    
    if request.method == 'POST':
        username = request.form.get('username')
        email = request.form.get('email')
        password = request.form.get('password')
        confirm_password = request.form.get('confirm_password')
        role = request.form.get('role', 'employee')
        
        # Validation
        if not all([username, email, password, confirm_password]):
            flash('Vui lòng điền đầy đủ thông tin.', 'error')
            return render_template('auth/register.html')
        
        if password != confirm_password:
            flash('Mật khẩu xác nhận không khớp.', 'error')
            return render_template('auth/register.html')
        
        if len(password) < 6:
            flash('Mật khẩu phải có ít nhất 6 ký tự.', 'error')
            return render_template('auth/register.html')
        
        # Check if user already exists
        if User.query.filter_by(username=username).first():
            flash('Tên đăng nhập đã tồn tại.', 'error')
            return render_template('auth/register.html')
        
        if User.query.filter_by(email=email).first():
            flash('Email đã được sử dụng.', 'error')
            return render_template('auth/register.html')
        
        # Create new user
        user = User(username=username, email=email, role=role)
        user.set_password(password)
        
        try:
            db.session.add(user)
            db.session.commit()
            flash('Đăng ký thành công! Vui lòng đăng nhập.', 'success')
            return redirect(url_for('auth.login'))
        except Exception as e:
            db.session.rollback()
            flash('Có lỗi xảy ra khi tạo tài khoản.', 'error')
            return render_template('auth/register.html')
    
    return render_template('auth/register.html')

@bp.route('/change-password', methods=['GET', 'POST'])
@login_required
def change_password():
    if request.method == 'POST':
        current_password = request.form.get('current_password')
        new_password = request.form.get('new_password')
        confirm_password = request.form.get('confirm_password')
        
        if not all([current_password, new_password, confirm_password]):
            flash('Vui lòng điền đầy đủ thông tin.', 'error')
            return render_template('auth/change_password.html')
        
        if not current_user.check_password(current_password):
            flash('Mật khẩu hiện tại không đúng.', 'error')
            return render_template('auth/change_password.html')
        
        if new_password != confirm_password:
            flash('Mật khẩu mới và xác nhận không khớp.', 'error')
            return render_template('auth/change_password.html')
        
        if len(new_password) < 6:
            flash('Mật khẩu mới phải có ít nhất 6 ký tự.', 'error')
            return render_template('auth/change_password.html')
        
        current_user.set_password(new_password)
        db.session.commit()
        
        flash('Đổi mật khẩu thành công!', 'success')
        return redirect(url_for('main.dashboard'))
    
    return render_template('auth/change_password.html')