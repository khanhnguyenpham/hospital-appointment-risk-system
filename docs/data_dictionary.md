# Từ điển dữ liệu

| Cột | Kiểu | Diễn giải |
|---|---|---|
| `appointment_id` | string | ID lịch hẹn duy nhất |
| `patient_id` | string | Chuỗi băm giả lập; không phải người thật |
| `appointment_date` | date | Ngày dự kiến khám |
| `booked_at` | datetime | Thời điểm đặt lịch |
| `department` | category | Khoa ngoại trú |
| `appointment_hour` | integer | Giờ khám, từ 7 đến 16 |
| `age_group` | category | Nhóm tuổi, không dùng tuổi chính xác |
| `district` | category | Khu vực cư trú mức tổng quát |
| `insurance_type` | category | BHYT, bảo hiểm tư hoặc tự chi trả |
| `prior_visits` | integer | Số lần khám trước trong lịch sử tổng hợp |
| `prior_no_shows` | integer | Số lần bỏ hẹn trước |
| `reminder_sent` | boolean | Đã ghi nhận gửi nhắc lịch hay chưa |
| `status` | category | `Completed`, `No-show`, `Cancelled` |
| `arrival_time` | datetime | Thời điểm đến nếu đã khám |
| `service_start_time` | datetime | Thời điểm bắt đầu phục vụ |
| `wait_minutes` | float | Phút chờ từ lúc đến tới lúc được phục vụ |
| `consultation_minutes` | float | Thời lượng khám tổng hợp |
| `no_show` | boolean | Target; bằng 1 khi status là `No-show` |
| `lead_days` | integer | Số ngày từ đặt lịch đến ngày khám |
| `weekday` | integer | Thứ Hai = 0, Chủ Nhật = 6 |
| `month` | integer | Tháng 1–12 |

Các cột thời gian sau sự kiện như `arrival_time`, `service_start_time`, `wait_minutes` và `status` tuyệt đối không đi vào mô hình dự đoán trước lịch hẹn.
