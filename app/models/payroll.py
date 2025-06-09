from datetime import datetime, date
from app import db

class Payroll(db.Model):
    __tablename__ = 'payrolls'
    
    id = db.Column(db.Integer, primary_key=True)
    employee_id = db.Column(db.Integer, db.ForeignKey('employees.id'), nullable=False)
    
    # Period
    pay_period_start = db.Column(db.Date, nullable=False)
    pay_period_end = db.Column(db.Date, nullable=False)
    pay_date = db.Column(db.Date, nullable=False)
    
    # Basic salary
    basic_salary = db.Column(db.Numeric(12, 2), nullable=False)
    
    # Allowances
    housing_allowance = db.Column(db.Numeric(10, 2), default=0)
    transport_allowance = db.Column(db.Numeric(10, 2), default=0)
    meal_allowance = db.Column(db.Numeric(10, 2), default=0)
    other_allowances = db.Column(db.Numeric(10, 2), default=0)
    
    # Overtime
    overtime_hours = db.Column(db.Float, default=0)
    overtime_rate = db.Column(db.Numeric(10, 2), default=0)
    overtime_pay = db.Column(db.Numeric(10, 2), default=0)
    
    # Bonuses
    performance_bonus = db.Column(db.Numeric(10, 2), default=0)
    holiday_bonus = db.Column(db.Numeric(10, 2), default=0)
    other_bonuses = db.Column(db.Numeric(10, 2), default=0)
    
    # Deductions
    tax_deduction = db.Column(db.Numeric(10, 2), default=0)
    insurance_deduction = db.Column(db.Numeric(10, 2), default=0)
    loan_deduction = db.Column(db.Numeric(10, 2), default=0)
    other_deductions = db.Column(db.Numeric(10, 2), default=0)
    
    # Totals
    gross_pay = db.Column(db.Numeric(12, 2), nullable=False)
    total_deductions = db.Column(db.Numeric(12, 2), nullable=False)
    net_pay = db.Column(db.Numeric(12, 2), nullable=False)
    
    # Status
    status = db.Column(db.String(20), default='draft')  # draft, approved, paid
    approved_by = db.Column(db.Integer, db.ForeignKey('users.id'))
    approved_at = db.Column(db.DateTime)
    
    # Notes
    notes = db.Column(db.Text)
    
    # Timestamps
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    updated_at = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    
    # Relationships
    approver = db.relationship('User', foreign_keys=[approved_by])
    
    def calculate_totals(self):
        """Calculate gross pay, total deductions, and net pay"""
        # Calculate gross pay
        self.gross_pay = (
            self.basic_salary +
            self.housing_allowance +
            self.transport_allowance +
            self.meal_allowance +
            self.other_allowances +
            self.overtime_pay +
            self.performance_bonus +
            self.holiday_bonus +
            self.other_bonuses
        )
        
        # Calculate total deductions
        self.total_deductions = (
            self.tax_deduction +
            self.insurance_deduction +
            self.loan_deduction +
            self.other_deductions
        )
        
        # Calculate net pay
        self.net_pay = self.gross_pay - self.total_deductions
    
    def calculate_overtime_pay(self):
        """Calculate overtime pay based on hours and rate"""
        if self.overtime_hours and self.overtime_rate:
            self.overtime_pay = self.overtime_hours * self.overtime_rate
    
    @staticmethod
    def generate_payroll_for_employee(employee, pay_period_start, pay_period_end):
        """Generate payroll for an employee for a specific period"""
        from app.models.attendance import Attendance
        
        # Get attendance records for the period
        attendances = Attendance.query.filter(
            Attendance.employee_id == employee.id,
            Attendance.date >= pay_period_start,
            Attendance.date <= pay_period_end
        ).all()
        
        # Calculate total overtime hours
        total_overtime = sum(att.overtime_hours or 0 for att in attendances)
        
        # Create payroll record
        payroll = Payroll(
            employee_id=employee.id,
            pay_period_start=pay_period_start,
            pay_period_end=pay_period_end,
            pay_date=pay_period_end,  # Default to end of period
            basic_salary=employee.salary or 0,
            overtime_hours=total_overtime,
            overtime_rate=employee.salary / 160 * 1.5 if employee.salary else 0  # 1.5x hourly rate
        )
        
        payroll.calculate_overtime_pay()
        payroll.calculate_totals()
        
        return payroll
    
    def __repr__(self):
        return f'<Payroll {self.employee.full_name} - {self.pay_period_start} to {self.pay_period_end}>'