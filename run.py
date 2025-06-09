from app import create_app, db
from app.models import User, Employee, Attendance, Payroll, Benefit, Reward, JobPosting, Application

app = create_app()

@app.shell_context_processor
def make_shell_context():
    return {
        'db': db, 
        'User': User, 
        'Employee': Employee,
        'Attendance': Attendance,
        'Payroll': Payroll,
        'Benefit': Benefit,
        'Reward': Reward,
        'JobPosting': JobPosting,
        'Application': Application
    }

@app.cli.command()
def init_db():
    """Initialize the database."""
    db.create_all()
    print('Database initialized.')

@app.cli.command()
def create_admin():
    """Create admin user."""
    admin = User.query.filter_by(username='admin').first()
    if admin:
        print('Admin user already exists.')
        return
    
    admin = User(
        username='admin',
        email='admin@company.com',
        role='admin'
    )
    admin.set_password('admin123')
    
    db.session.add(admin)
    db.session.commit()
    print('Admin user created: admin/admin123')

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=12000, debug=True)