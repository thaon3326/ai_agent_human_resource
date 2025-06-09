from datetime import datetime, date
from app import db

class Reward(db.Model):
    __tablename__ = 'rewards'
    
    id = db.Column(db.Integer, primary_key=True)
    employee_id = db.Column(db.Integer, db.ForeignKey('employees.id'), nullable=False)
    
    # Reward details
    reward_type = db.Column(db.String(50), nullable=False)  # bonus, recognition, promotion, gift, etc.
    title = db.Column(db.String(100), nullable=False)
    description = db.Column(db.Text)
    reason = db.Column(db.Text)  # Reason for the reward
    
    # Financial value
    monetary_value = db.Column(db.Numeric(10, 2), default=0)
    currency = db.Column(db.String(3), default='VND')
    
    # Dates
    award_date = db.Column(db.Date, nullable=False, default=date.today)
    effective_date = db.Column(db.Date)  # When the reward takes effect
    
    # Status
    status = db.Column(db.String(20), default='pending')  # pending, approved, rejected, paid
    
    # Approval workflow
    nominated_by = db.Column(db.Integer, db.ForeignKey('users.id'))
    approved_by = db.Column(db.Integer, db.ForeignKey('users.id'))
    approved_at = db.Column(db.DateTime)
    rejection_reason = db.Column(db.Text)
    
    # Performance metrics (if applicable)
    performance_period_start = db.Column(db.Date)
    performance_period_end = db.Column(db.Date)
    performance_score = db.Column(db.Float)
    kpi_achievements = db.Column(db.JSON)  # Store KPI data
    
    # Additional details
    public_recognition = db.Column(db.Boolean, default=False)  # Whether to announce publicly
    certificate_issued = db.Column(db.Boolean, default=False)
    certificate_path = db.Column(db.String(255))
    
    # Timestamps
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    updated_at = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    
    # Relationships
    nominator = db.relationship('User', foreign_keys=[nominated_by])
    approver = db.relationship('User', foreign_keys=[approved_by])
    
    @staticmethod
    def get_reward_types():
        """Get list of available reward types"""
        return [
            ('performance_bonus', 'Thưởng hiệu suất'),
            ('achievement_bonus', 'Thưởng thành tích'),
            ('project_completion', 'Thưởng hoàn thành dự án'),
            ('employee_of_month', 'Nhân viên xuất sắc tháng'),
            ('employee_of_year', 'Nhân viên xuất sắc năm'),
            ('innovation_award', 'Giải thưởng sáng tạo'),
            ('teamwork_award', 'Giải thưởng làm việc nhóm'),
            ('leadership_award', 'Giải thưởng lãnh đạo'),
            ('customer_service', 'Giải thưởng dịch vụ khách hàng'),
            ('attendance_bonus', 'Thưởng chuyên cần'),
            ('loyalty_bonus', 'Thưởng gắn bó'),
            ('promotion', 'Thăng chức'),
            ('salary_increase', 'Tăng lương'),
            ('gift_voucher', 'Phiếu quà tặng'),
            ('training_opportunity', 'Cơ hội đào tạo'),
            ('other', 'Khác')
        ]
    
    def approve(self, approver_id):
        """Approve the reward"""
        self.status = 'approved'
        self.approved_by = approver_id
        self.approved_at = datetime.utcnow()
    
    def reject(self, approver_id, reason):
        """Reject the reward"""
        self.status = 'rejected'
        self.approved_by = approver_id
        self.approved_at = datetime.utcnow()
        self.rejection_reason = reason
    
    @property
    def is_pending(self):
        return self.status == 'pending'
    
    @property
    def is_approved(self):
        return self.status == 'approved'
    
    @property
    def is_rejected(self):
        return self.status == 'rejected'
    
    def __repr__(self):
        return f'<Reward {self.employee.full_name} - {self.title}>'