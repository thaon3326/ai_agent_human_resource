from datetime import datetime, date, time, timedelta
from app import db

class Attendance(db.Model):
    __tablename__ = 'attendances'
    
    id = db.Column(db.Integer, primary_key=True)
    employee_id = db.Column(db.Integer, db.ForeignKey('employees.id'), nullable=False)
    date = db.Column(db.Date, nullable=False, default=date.today)
    
    # Time tracking
    check_in = db.Column(db.Time)
    check_out = db.Column(db.Time)
    break_start = db.Column(db.Time)
    break_end = db.Column(db.Time)
    
    # Calculated fields
    total_hours = db.Column(db.Float, default=0.0)
    overtime_hours = db.Column(db.Float, default=0.0)
    
    # Status
    status = db.Column(db.String(20), default='present')  # present, absent, late, half_day, sick_leave, vacation
    notes = db.Column(db.Text)
    
    # Approval
    approved_by = db.Column(db.Integer, db.ForeignKey('users.id'))
    approved_at = db.Column(db.DateTime)
    
    # Timestamps
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    updated_at = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    
    # Relationships
    approver = db.relationship('User', foreign_keys=[approved_by])
    
    def calculate_hours(self):
        """Calculate total hours and overtime"""
        if self.check_in and self.check_out:
            # Convert time to datetime for calculation
            check_in_dt = datetime.combine(date.today(), self.check_in)
            check_out_dt = datetime.combine(date.today(), self.check_out)
            
            # Handle overnight shifts
            if check_out_dt < check_in_dt:
                check_out_dt = datetime.combine(date.today() + timedelta(days=1), self.check_out)
            
            total_minutes = (check_out_dt - check_in_dt).total_seconds() / 60
            
            # Subtract break time if available
            if self.break_start and self.break_end:
                break_start_dt = datetime.combine(date.today(), self.break_start)
                break_end_dt = datetime.combine(date.today(), self.break_end)
                break_minutes = (break_end_dt - break_start_dt).total_seconds() / 60
                total_minutes -= break_minutes
            
            self.total_hours = round(total_minutes / 60, 2)
            
            # Calculate overtime (assuming 8 hours is standard)
            standard_hours = 8.0
            if self.total_hours > standard_hours:
                self.overtime_hours = round(self.total_hours - standard_hours, 2)
            else:
                self.overtime_hours = 0.0
    
    @property
    def is_late(self):
        """Check if employee was late (assuming 9:00 AM start time)"""
        if self.check_in:
            standard_start = time(9, 0)  # 9:00 AM
            return self.check_in > standard_start
        return False
    
    @property
    def is_early_leave(self):
        """Check if employee left early (assuming 5:00 PM end time)"""
        if self.check_out:
            standard_end = time(17, 0)  # 5:00 PM
            return self.check_out < standard_end
        return False
    
    def __repr__(self):
        return f'<Attendance {self.employee.full_name} - {self.date}>'