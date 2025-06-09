from datetime import datetime, date
from app import db

class Employee(db.Model):
    __tablename__ = 'employees'
    
    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey('users.id'), nullable=False)
    employee_id = db.Column(db.String(20), unique=True, nullable=False)
    
    # Personal Information
    first_name = db.Column(db.String(50), nullable=False)
    last_name = db.Column(db.String(50), nullable=False)
    full_name = db.Column(db.String(100), nullable=False)
    date_of_birth = db.Column(db.Date)
    gender = db.Column(db.String(10))
    phone = db.Column(db.String(20))
    address = db.Column(db.Text)
    emergency_contact = db.Column(db.String(100))
    emergency_phone = db.Column(db.String(20))
    
    # Work Information
    department = db.Column(db.String(50))
    position = db.Column(db.String(50))
    hire_date = db.Column(db.Date, default=date.today)
    employment_type = db.Column(db.String(20), default='full_time')  # full_time, part_time, contract
    salary = db.Column(db.Numeric(12, 2))
    manager_id = db.Column(db.Integer, db.ForeignKey('employees.id'))
    
    # Status
    status = db.Column(db.String(20), default='active')  # active, inactive, terminated
    termination_date = db.Column(db.Date)
    
    # Documents
    avatar = db.Column(db.String(255))
    documents = db.Column(db.JSON)  # Store document paths and types
    
    # Timestamps
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    updated_at = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    
    # Relationships
    manager = db.relationship('Employee', remote_side=[id], backref='subordinates')
    attendances = db.relationship('Attendance', backref='employee', lazy='dynamic')
    payrolls = db.relationship('Payroll', backref='employee', lazy='dynamic')
    benefits = db.relationship('Benefit', backref='employee', lazy='dynamic')
    rewards = db.relationship('Reward', backref='employee', lazy='dynamic')
    
    def __init__(self, **kwargs):
        super(Employee, self).__init__(**kwargs)
        if self.full_name is None and self.first_name and self.last_name:
            self.full_name = f"{self.first_name} {self.last_name}"
    
    @property
    def age(self):
        if self.date_of_birth:
            today = date.today()
            return today.year - self.date_of_birth.year - ((today.month, today.day) < (self.date_of_birth.month, self.date_of_birth.day))
        return None
    
    @property
    def years_of_service(self):
        if self.hire_date:
            today = date.today()
            return today.year - self.hire_date.year - ((today.month, today.day) < (self.hire_date.month, self.hire_date.day))
        return 0
    
    def get_current_month_attendance(self):
        """Get attendance records for current month"""
        from datetime import datetime
        current_month = datetime.now().month
        current_year = datetime.now().year
        return self.attendances.filter(
            db.extract('month', Attendance.date) == current_month,
            db.extract('year', Attendance.date) == current_year
        ).all()
    
    def __repr__(self):
        return f'<Employee {self.employee_id}: {self.full_name}>'