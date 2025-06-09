from flask import Flask
from flask_sqlalchemy import SQLAlchemy
from flask_login import LoginManager
from flask_migrate import Migrate
from config import Config

db = SQLAlchemy()
login_manager = LoginManager()
migrate = Migrate()

def create_app(config_class=Config):
    app = Flask(__name__)
    app.config.from_object(config_class)
    
    # Initialize extensions
    db.init_app(app)
    login_manager.init_app(app)
    migrate.init_app(app, db)
    
    # Configure login manager
    login_manager.login_view = 'auth.login'
    login_manager.login_message = 'Vui lòng đăng nhập để truy cập trang này.'
    login_manager.login_message_category = 'info'
    
    # Register blueprints
    from app.routes.auth import bp as auth_bp
    app.register_blueprint(auth_bp, url_prefix='/auth')
    
    from app.routes.main import bp as main_bp
    app.register_blueprint(main_bp)
    
    from app.routes.employee import bp as employee_bp
    app.register_blueprint(employee_bp, url_prefix='/employee')
    
    from app.routes.attendance import bp as attendance_bp
    app.register_blueprint(attendance_bp, url_prefix='/attendance')
    
    from app.routes.payroll import bp as payroll_bp
    app.register_blueprint(payroll_bp, url_prefix='/payroll')
    
    from app.routes.benefits import bp as benefits_bp
    app.register_blueprint(benefits_bp, url_prefix='/benefits')
    
    from app.routes.recruitment import bp as recruitment_bp
    app.register_blueprint(recruitment_bp, url_prefix='/recruitment')
    
    from app.routes.admin import bp as admin_bp
    app.register_blueprint(admin_bp, url_prefix='/admin')
    
    return app

from app import models