from datetime import datetime, date
from app import db

class Benefit(db.Model):
    __tablename__ = 'benefits'
    
    id = db.Column(db.Integer, primary_key=True)
    employee_id = db.Column(db.Integer, db.ForeignKey('employees.id'), nullable=False)
    
    # Benefit details
    benefit_type = db.Column(db.String(50), nullable=False)  # health_insurance, life_insurance, retirement, vacation, etc.
    benefit_name = db.Column(db.String(100), nullable=False)
    description = db.Column(db.Text)
    
    # Financial details
    employer_contribution = db.Column(db.Numeric(10, 2), default=0)
    employee_contribution = db.Column(db.Numeric(10, 2), default=0)
    total_value = db.Column(db.Numeric(10, 2), default=0)
    
    # Dates
    start_date = db.Column(db.Date, nullable=False)
    end_date = db.Column(db.Date)
    
    # Status
    status = db.Column(db.String(20), default='active')  # active, inactive, pending, expired
    
    # Provider information
    provider_name = db.Column(db.String(100))
    provider_contact = db.Column(db.String(100))
    policy_number = db.Column(db.String(50))
    
    # Additional details
    coverage_details = db.Column(db.JSON)  # Store coverage specifics
    documents = db.Column(db.JSON)  # Store document paths
    
    # Approval
    approved_by = db.Column(db.Integer, db.ForeignKey('users.id'))
    approved_at = db.Column(db.DateTime)
    
    # Timestamps
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    updated_at = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    
    # Relationships
    approver = db.relationship('User', foreign_keys=[approved_by])
    
    @property
    def is_active(self):
        """Check if benefit is currently active"""
        today = date.today()
        if self.status != 'active':
            return False
        if self.start_date > today:
            return False
        if self.end_date and self.end_date < today:
            return False
        return True
    
    @property
    def days_until_expiry(self):
        """Calculate days until benefit expires"""
        if self.end_date:
            today = date.today()
            if self.end_date > today:
                return (self.end_date - today).days
        return None
    
    def calculate_total_value(self):
        """Calculate total benefit value"""
        self.total_value = (self.employer_contribution or 0) + (self.employee_contribution or 0)
    
    @staticmethod
    def get_benefit_types():
        """Get list of available benefit types"""
        return [
            ('health_insurance', 'Bảo hiểm y tế'),
            ('life_insurance', 'Bảo hiểm nhân thọ'),
            ('dental_insurance', 'Bảo hiểm nha khoa'),
            ('retirement_plan', 'Kế hoạch hưu trí'),
            ('vacation_days', 'Ngày nghỉ phép'),
            ('sick_leave', 'Nghỉ ốm'),
            ('maternity_leave', 'Nghỉ thai sản'),
            ('training_budget', 'Ngân sách đào tạo'),
            ('gym_membership', 'Thành viên phòng gym'),
            ('meal_vouchers', 'Phiếu ăn'),
            ('transport_allowance', 'Phụ cấp đi lại'),
            ('phone_allowance', 'Phụ cấp điện thoại'),
            ('other', 'Khác')
        ]
    
    def __repr__(self):
        return f'<Benefit {self.employee.full_name} - {self.benefit_name}>'