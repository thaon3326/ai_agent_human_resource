// HR Management System JavaScript

$(document).ready(function() {
    // Initialize tooltips
    var tooltipTriggerList = [].slice.call(document.querySelectorAll('[data-bs-toggle="tooltip"]'));
    var tooltipList = tooltipTriggerList.map(function (tooltipTriggerEl) {
        return new bootstrap.Tooltip(tooltipTriggerEl);
    });

    // Initialize popovers
    var popoverTriggerList = [].slice.call(document.querySelectorAll('[data-bs-toggle="popover"]'));
    var popoverList = popoverTriggerList.map(function (popoverTriggerEl) {
        return new bootstrap.Popover(popoverTriggerEl);
    });

    // Real-time clock
    updateClock();
    setInterval(updateClock, 1000);

    // Auto-hide alerts after 5 seconds
    setTimeout(function() {
        $('.alert').fadeOut('slow');
    }, 5000);

    // Confirm delete actions
    $('.btn-delete').on('click', function(e) {
        if (!confirm('Bạn có chắc chắn muốn xóa?')) {
            e.preventDefault();
        }
    });

    // Form validation
    $('form').on('submit', function() {
        $(this).find('button[type="submit"]').prop('disabled', true).html('<span class="spinner"></span> Đang xử lý...');
    });

    // Search functionality
    $('#searchInput').on('keyup', function() {
        var value = $(this).val().toLowerCase();
        $('#searchResults tr').filter(function() {
            $(this).toggle($(this).text().toLowerCase().indexOf(value) > -1);
        });
    });

    // Attendance functions
    initAttendance();
});

function updateClock() {
    var now = new Date();
    var timeString = now.toLocaleTimeString('vi-VN', {
        hour12: false,
        hour: '2-digit',
        minute: '2-digit',
        second: '2-digit'
    });
    var dateString = now.toLocaleDateString('vi-VN', {
        weekday: 'long',
        year: 'numeric',
        month: 'long',
        day: 'numeric'
    });
    
    $('#currentTime').text(timeString);
    $('#currentDate').text(dateString);
}

function initAttendance() {
    // Check attendance status on page load
    if ($('#attendanceStatus').length) {
        checkAttendanceStatus();
    }

    // Attendance button handlers
    $('#checkInBtn').on('click', function() {
        performAttendanceAction('check-in', $(this));
    });

    $('#checkOutBtn').on('click', function() {
        performAttendanceAction('check-out', $(this));
    });

    $('#breakStartBtn').on('click', function() {
        performAttendanceAction('break-start', $(this));
    });

    $('#breakEndBtn').on('click', function() {
        performAttendanceAction('break-end', $(this));
    });
}

function checkAttendanceStatus() {
    var employeeId = $('#attendanceStatus').data('employee-id');
    if (!employeeId) return;

    $.get('/attendance/status/' + employeeId)
        .done(function(data) {
            updateAttendanceUI(data);
        })
        .fail(function() {
            console.log('Failed to check attendance status');
        });
}

function updateAttendanceUI(status) {
    $('#checkInBtn').prop('disabled', status.checked_in);
    $('#checkOutBtn').prop('disabled', !status.checked_in || status.checked_out);
    $('#breakStartBtn').prop('disabled', !status.checked_in || status.on_break || status.checked_out);
    $('#breakEndBtn').prop('disabled', !status.on_break);

    if (status.check_in_time) {
        $('#checkInTime').text('Check-in: ' + status.check_in_time);
    }
    if (status.check_out_time) {
        $('#checkOutTime').text('Check-out: ' + status.check_out_time);
    }
    if (status.total_hours) {
        $('#totalHours').text('Tổng giờ: ' + status.total_hours);
    }
}

function performAttendanceAction(action, button) {
    var originalText = button.html();
    button.prop('disabled', true).html('<span class="spinner"></span> Đang xử lý...');

    $.post('/attendance/' + action)
        .done(function(response) {
            if (response.success) {
                showAlert('success', response.message);
                checkAttendanceStatus(); // Refresh status
            } else {
                showAlert('error', response.message);
            }
        })
        .fail(function() {
            showAlert('error', 'Có lỗi xảy ra khi thực hiện thao tác.');
        })
        .always(function() {
            button.prop('disabled', false).html(originalText);
        });
}

function showAlert(type, message) {
    var alertClass = type === 'error' ? 'alert-danger' : 'alert-' + type;
    var alertHtml = '<div class="alert ' + alertClass + ' alert-dismissible fade show" role="alert">' +
                    message +
                    '<button type="button" class="btn-close" data-bs-dismiss="alert"></button>' +
                    '</div>';
    
    $('#alertContainer').html(alertHtml);
    
    // Auto-hide after 5 seconds
    setTimeout(function() {
        $('.alert').fadeOut('slow');
    }, 5000);
}

// Chart functions
function createChart(canvasId, type, data, options) {
    var ctx = document.getElementById(canvasId);
    if (!ctx) return;

    return new Chart(ctx, {
        type: type,
        data: data,
        options: options || {}
    });
}

// Export functions
function exportToExcel(tableId, filename) {
    var table = document.getElementById(tableId);
    if (!table) return;

    var wb = XLSX.utils.table_to_book(table);
    XLSX.writeFile(wb, filename + '.xlsx');
}

function exportToPDF(elementId, filename) {
    var element = document.getElementById(elementId);
    if (!element) return;

    html2pdf()
        .from(element)
        .save(filename + '.pdf');
}

// Utility functions
function formatCurrency(amount) {
    return new Intl.NumberFormat('vi-VN', {
        style: 'currency',
        currency: 'VND'
    }).format(amount);
}

function formatDate(dateString) {
    var date = new Date(dateString);
    return date.toLocaleDateString('vi-VN');
}

function formatDateTime(dateString) {
    var date = new Date(dateString);
    return date.toLocaleString('vi-VN');
}

// Form helpers
function validateEmail(email) {
    var re = /^[^\s@]+@[^\s@]+\.[^\s@]+$/;
    return re.test(email);
}

function validatePhone(phone) {
    var re = /^[0-9]{10,11}$/;
    return re.test(phone.replace(/\s/g, ''));
}

// File upload helpers
function previewImage(input, previewId) {
    if (input.files && input.files[0]) {
        var reader = new FileReader();
        reader.onload = function(e) {
            $('#' + previewId).attr('src', e.target.result).show();
        };
        reader.readAsDataURL(input.files[0]);
    }
}

// Data table initialization
function initDataTable(tableId, options) {
    var defaultOptions = {
        language: {
            url: '//cdn.datatables.net/plug-ins/1.11.5/i18n/vi.json'
        },
        responsive: true,
        pageLength: 25,
        order: [[0, 'desc']]
    };

    var finalOptions = $.extend({}, defaultOptions, options);
    return $('#' + tableId).DataTable(finalOptions);
}

// Notification system
function showNotification(title, message, type) {
    if ('Notification' in window && Notification.permission === 'granted') {
        new Notification(title, {
            body: message,
            icon: '/static/images/logo.png'
        });
    }
}

function requestNotificationPermission() {
    if ('Notification' in window && Notification.permission === 'default') {
        Notification.requestPermission();
    }
}

// Auto-save form data
function enableAutoSave(formId, interval) {
    interval = interval || 30000; // 30 seconds default

    setInterval(function() {
        var formData = $('#' + formId).serialize();
        localStorage.setItem('autosave_' + formId, formData);
    }, interval);
}

function restoreAutoSave(formId) {
    var savedData = localStorage.getItem('autosave_' + formId);
    if (savedData) {
        var params = new URLSearchParams(savedData);
        params.forEach(function(value, key) {
            var input = $('#' + formId + ' [name="' + key + '"]');
            if (input.length) {
                input.val(value);
            }
        });
    }
}

function clearAutoSave(formId) {
    localStorage.removeItem('autosave_' + formId);
}

// Print functionality
function printElement(elementId) {
    var element = document.getElementById(elementId);
    if (!element) return;

    var printWindow = window.open('', '_blank');
    printWindow.document.write('<html><head><title>In tài liệu</title>');
    printWindow.document.write('<link rel="stylesheet" href="/static/css/style.css">');
    printWindow.document.write('</head><body>');
    printWindow.document.write(element.innerHTML);
    printWindow.document.write('</body></html>');
    printWindow.document.close();
    printWindow.print();
}