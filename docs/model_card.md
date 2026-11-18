# Model card — rủi ro bỏ hẹn ngoại trú

## Mục đích sử dụng

Mô hình xếp hạng các lịch hẹn cần nhân viên xem xét để ưu tiên nhắc lịch. Điểm số **không được dùng** để hủy, trì hoãn, từ chối khám hoặc đưa ra quyết định lâm sàng.

## Dữ liệu và cách đánh giá

- 100% dữ liệu tổng hợp được tạo trong repository; không có hồ sơ bệnh nhân thật.
- Chia train/validation/test theo thời gian để tránh đưa thông tin tương lai vào huấn luyện.
- Tập test là giai đoạn 2026-07-20 đến 2026-10-31.
- Ngưỡng được chọn trên validation với giới hạn tối đa 30% lịch hẹn phải xem xét.

## Kết quả tham chiếu

| Chỉ số | Logistic regression | Baseline theo tỷ lệ lớp |
|---|---:|---:|
| ROC-AUC | 0.6779 | 0.5000 |
| Brier score | 0.1521 | 0.1631 |
| Expected calibration error | 0.0288 | 0.0260 |
| Precision | 0.3468 | 0.0000 |
| Recall | 0.5172 | 0.0000 |
| F1 | 0.4152 | 0.0000 |

Ngưỡng quyết định: **0.20**. Tỷ lệ đưa vào hàng đợi trên test: **30.4%**.

## Giới hạn và kiểm soát

- Kết quả trên dữ liệu tổng hợp không chứng minh hiệu quả tại bệnh viện thật.
- Biến `reminder_sent` chỉ phản ánh mối liên hệ trong dữ liệu, không chứng minh tác động nhân quả.
- Theo dõi PSI, tỷ lệ đưa vào hàng đợi và hiệu năng theo khoa trước khi dựa vào kết quả.
- Luôn giữ người phụ trách trong vòng quyết định và ghi lại hành động vận hành.
- Cần đánh giá riêng tư, bảo mật, thiên lệch và an toàn trước mọi thử nghiệm thực tế.

Phiên bản mô hình: `v1-5830ce85` · Schema: `1.0`
