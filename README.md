# Hệ thống Quản lý Nhân sự (HR Management System)

Một hệ thống quản lý nhân sự hoàn chỉnh được xây dựng bằng Python Flask, hỗ trợ quản lý toàn diện các hoạt động nhân sự trong doanh nghiệp.

## 🚀 Tính năng chính

### 👥 Quản lý Nhân viên
- Thêm, sửa, xóa thông tin nhân viên
- Quản lý hồ sơ cá nhân chi tiết
- Phân cấp quản lý (Manager - Subordinate)
- Upload và quản lý avatar nhân viên

### ⏰ Chấm công
- Check-in/Check-out trực tuyến
- Quản lý giờ nghỉ giải lao
- Tính toán tự động giờ làm việc và overtime
- Báo cáo chấm công theo tháng/năm

### 💰 Quản lý Lương
- Tạo bảng lương tự động dựa trên chấm công
- Quản lý phụ cấp, thưởng, khấu trừ
- Tính toán thuế và bảo hiểm
- Xuất báo cáo lương theo phòng ban

### 🎁 Quản lý Phúc lợi
- Quản lý các gói phúc lợi nhân viên
- Theo dõi bảo hiểm y tế, xã hội
- Quản lý ngày nghỉ phép, nghỉ ốm
- Báo cáo tổng hợp phúc lợi

### 🏆 Khen thưởng
- Đề xuất và phê duyệt khen thưởng
- Quản lý các loại thưởng khác nhau
- Theo dõi hiệu suất làm việc
- Lịch sử khen thưởng nhân viên

### 📋 Tuyển dụng
- Đăng tin tuyển dụng
- Quản lý hồ sơ ứng viên
- Lên lịch phỏng vấn
- Theo dõi quy trình tuyển dụng

### 🔐 Phân quyền người dùng
- **Admin**: Toàn quyền quản lý hệ thống
- **HR**: Quản lý nhân sự, lương, phúc lợi, tuyển dụng
- **Leader**: Quản lý team, xem báo cáo nhóm
- **Employee**: Xem thông tin cá nhân, chấm công

## 🛠️ Công nghệ sử dụng

- **Backend**: Python Flask
- **Database**: SQLite (có thể chuyển sang PostgreSQL)
- **ORM**: SQLAlchemy
- **Authentication**: Flask-Login
- **Frontend**: Bootstrap 5, jQuery
- **Icons**: Font Awesome

## 📦 Cài đặt

### 1. Clone repository
```bash
git clone <repository-url>
cd ai_agent_human_resource
```

### 2. Cài đặt dependencies
```bash
pip install -r requirements.txt
```

### 3. Cấu hình môi trường
Tạo file `.env` hoặc chỉnh sửa file có sẵn:
```env
SECRET_KEY=your-secret-key-here
DATABASE_URL=sqlite:///hr_management.db
FLASK_ENV=development
FLASK_DEBUG=True
```

### 4. Khởi tạo database
```bash
python -c "
from app import create_app, db
from app.models.user import User

app = create_app()
with app.app_context():
    db.create_all()
    
    # Tạo admin user
    admin = User(username='admin', email='admin@company.com', role='admin')
    admin.set_password('admin123')
    db.session.add(admin)
    db.session.commit()
    print('Database initialized!')
"
```

### 5. Chạy ứng dụng
```bash
python run.py
```

Ứng dụng sẽ chạy tại: http://localhost:12000

## 👤 Tài khoản demo

Hệ thống đã được tạo sẵn các tài khoản demo:

| Username | Password | Role | Mô tả |
|----------|----------|------|-------|
| admin | admin123 | Admin | Quản trị viên hệ thống |
| hr_manager | hr123 | HR | Nhân viên phòng nhân sự |
| team_leader | leader123 | Leader | Trưởng nhóm |
| employee1 | emp123 | Employee | Nhân viên |

## 📱 Giao diện

### Dashboard
- Dashboard riêng cho từng role
- Thống kê tổng quan
- Thao tác nhanh
- Thông báo quan trọng

### Responsive Design
- Tương thích với mobile, tablet
- Giao diện thân thiện, dễ sử dụng
- Màu sắc chuyên nghiệp

## 🔧 Cấu trúc dự án

```
ai_agent_human_resource/
├── app/
│   ├── __init__.py
│   ├── models/          # Database models
│   ├── routes/          # API routes
│   ├── templates/       # HTML templates
│   └── static/          # CSS, JS, images
├── config.py           # Cấu hình ứng dụng
├── requirements.txt    # Dependencies
├── run.py             # Entry point
└── README.md
```

## 🚀 Triển khai Production

### Sử dụng PostgreSQL
1. Cài đặt PostgreSQL
2. Tạo database
3. Cập nhật `DATABASE_URL` trong `.env`
4. Chạy migration

### Sử dụng Gunicorn
```bash
pip install gunicorn
gunicorn -w 4 -b 0.0.0.0:8000 run:app
```

### Sử dụng Docker
```dockerfile
FROM python:3.9
WORKDIR /app
COPY requirements.txt .
RUN pip install -r requirements.txt
COPY . .
CMD ["gunicorn", "-w", "4", "-b", "0.0.0.0:8000", "run:app"]
```

## 📈 Tính năng nâng cao

### Báo cáo và Thống kê
- Báo cáo chấm công theo phòng ban
- Thống kê lương theo tháng/quý/năm
- Phân tích hiệu suất nhân viên
- Export Excel/PDF

### Tích hợp
- Email notifications
- SMS alerts
- API endpoints
- Webhook support

### Bảo mật
- Password hashing
- Session management
- CSRF protection
- Input validation

## 🤝 Đóng góp

1. Fork repository
2. Tạo feature branch
3. Commit changes
4. Push to branch
5. Create Pull Request

## 📄 License

MIT License - xem file LICENSE để biết thêm chi tiết.

## 📞 Hỗ trợ

Nếu bạn gặp vấn đề hoặc có câu hỏi, vui lòng tạo issue trên GitHub.

---

**Phát triển bởi**: AI Agent
**Phiên bản**: 1.0.0
**Ngày cập nhật**: 2024
