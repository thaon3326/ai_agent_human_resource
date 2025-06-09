from datetime import datetime, date
from app import db

class JobPosting(db.Model):
    __tablename__ = 'job_postings'
    
    id = db.Column(db.Integer, primary_key=True)
    
    # Job details
    title = db.Column(db.String(100), nullable=False)
    department = db.Column(db.String(50), nullable=False)
    location = db.Column(db.String(100))
    employment_type = db.Column(db.String(20), default='full_time')  # full_time, part_time, contract, internship
    
    # Job description
    description = db.Column(db.Text, nullable=False)
    requirements = db.Column(db.Text)
    responsibilities = db.Column(db.Text)
    benefits = db.Column(db.Text)
    
    # Compensation
    salary_min = db.Column(db.Numeric(12, 2))
    salary_max = db.Column(db.Numeric(12, 2))
    salary_currency = db.Column(db.String(3), default='VND')
    
    # Dates
    posting_date = db.Column(db.Date, default=date.today)
    application_deadline = db.Column(db.Date)
    start_date = db.Column(db.Date)
    
    # Status
    status = db.Column(db.String(20), default='draft')  # draft, active, closed, cancelled
    positions_available = db.Column(db.Integer, default=1)
    positions_filled = db.Column(db.Integer, default=0)
    
    # Contact information
    contact_person = db.Column(db.String(100))
    contact_email = db.Column(db.String(120))
    contact_phone = db.Column(db.String(20))
    
    # Metadata
    created_by = db.Column(db.Integer, db.ForeignKey('users.id'), nullable=False)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    updated_at = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    
    # Relationships
    creator = db.relationship('User', foreign_keys=[created_by])
    applications = db.relationship('Application', backref='job_posting', lazy='dynamic', cascade='all, delete-orphan')
    
    @property
    def is_active(self):
        """Check if job posting is currently active"""
        today = date.today()
        return (self.status == 'active' and 
                (not self.application_deadline or self.application_deadline >= today) and
                self.positions_filled < self.positions_available)
    
    @property
    def applications_count(self):
        """Get total number of applications"""
        return self.applications.count()
    
    @property
    def pending_applications_count(self):
        """Get number of pending applications"""
        return self.applications.filter_by(status='pending').count()
    
    def __repr__(self):
        return f'<JobPosting {self.title} - {self.department}>'


class Application(db.Model):
    __tablename__ = 'applications'
    
    id = db.Column(db.Integer, primary_key=True)
    job_posting_id = db.Column(db.Integer, db.ForeignKey('job_postings.id'), nullable=False)
    
    # Applicant information
    first_name = db.Column(db.String(50), nullable=False)
    last_name = db.Column(db.String(50), nullable=False)
    email = db.Column(db.String(120), nullable=False)
    phone = db.Column(db.String(20))
    address = db.Column(db.Text)
    
    # Application details
    cover_letter = db.Column(db.Text)
    resume_path = db.Column(db.String(255))
    portfolio_path = db.Column(db.String(255))
    expected_salary = db.Column(db.Numeric(12, 2))
    available_start_date = db.Column(db.Date)
    
    # Status and workflow
    status = db.Column(db.String(20), default='pending')  # pending, reviewing, interview, offer, hired, rejected
    application_date = db.Column(db.Date, default=date.today)
    
    # Interview information
    interview_scheduled = db.Column(db.Boolean, default=False)
    interview_date = db.Column(db.DateTime)
    interview_location = db.Column(db.String(200))
    interview_notes = db.Column(db.Text)
    interviewer_id = db.Column(db.Integer, db.ForeignKey('users.id'))
    
    # Evaluation
    technical_score = db.Column(db.Integer)  # 1-10 scale
    communication_score = db.Column(db.Integer)  # 1-10 scale
    cultural_fit_score = db.Column(db.Integer)  # 1-10 scale
    overall_score = db.Column(db.Float)
    evaluation_notes = db.Column(db.Text)
    
    # Decision
    decision_date = db.Column(db.Date)
    decision_by = db.Column(db.Integer, db.ForeignKey('users.id'))
    rejection_reason = db.Column(db.Text)
    offer_details = db.Column(db.JSON)  # Store offer specifics
    
    # Timestamps
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    updated_at = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    
    # Relationships
    interviewer = db.relationship('User', foreign_keys=[interviewer_id])
    decision_maker = db.relationship('User', foreign_keys=[decision_by])
    
    @property
    def full_name(self):
        return f"{self.first_name} {self.last_name}"
    
    @property
    def days_since_application(self):
        """Calculate days since application was submitted"""
        return (date.today() - self.application_date).days
    
    def calculate_overall_score(self):
        """Calculate overall score from individual scores"""
        scores = [self.technical_score, self.communication_score, self.cultural_fit_score]
        valid_scores = [score for score in scores if score is not None]
        if valid_scores:
            self.overall_score = sum(valid_scores) / len(valid_scores)
    
    def schedule_interview(self, interview_date, location, interviewer_id):
        """Schedule an interview for the applicant"""
        self.interview_scheduled = True
        self.interview_date = interview_date
        self.interview_location = location
        self.interviewer_id = interviewer_id
        self.status = 'interview'
    
    def make_offer(self, offer_details, decision_maker_id):
        """Make an offer to the applicant"""
        self.status = 'offer'
        self.decision_date = date.today()
        self.decision_by = decision_maker_id
        self.offer_details = offer_details
    
    def hire(self, decision_maker_id):
        """Hire the applicant"""
        self.status = 'hired'
        self.decision_date = date.today()
        self.decision_by = decision_maker_id
        
        # Update job posting
        self.job_posting.positions_filled += 1
    
    def reject(self, reason, decision_maker_id):
        """Reject the applicant"""
        self.status = 'rejected'
        self.decision_date = date.today()
        self.decision_by = decision_maker_id
        self.rejection_reason = reason
    
    @staticmethod
    def get_status_choices():
        """Get list of application status choices"""
        return [
            ('pending', 'Chờ xử lý'),
            ('reviewing', 'Đang xem xét'),
            ('interview', 'Phỏng vấn'),
            ('offer', 'Đã gửi offer'),
            ('hired', 'Đã tuyển'),
            ('rejected', 'Từ chối')
        ]
    
    def __repr__(self):
        return f'<Application {self.full_name} - {self.job_posting.title}>'