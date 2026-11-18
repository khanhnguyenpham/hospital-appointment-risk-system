# Roadmap

Phiên bản hiện tại chứng minh một luồng AI Systems có thể tái lập từ dữ liệu đến serving và monitoring. Roadmap ghi rõ phần còn thiếu trước khi có thể nghĩ đến pilot; đây không phải danh sách tính năng đã hoàn thành.

## Ưu tiên gần

### Đánh giá xác suất và threshold

- Thêm reliability diagram để quan sát ECE theo từng khoảng xác suất.
- So sánh calibration methods chỉ trên validation, giữ test cho đánh giá cuối.
- Báo cáo ảnh hưởng của nhiều mức giới hạn hàng đợi thay vì cố định 30%.

### Theo dõi có trạng thái

- Lưu metric theo batch và model version.
- Dashboard xu hướng PSI, review rate và dữ liệu lỗi theo thời gian.
- Cảnh báo khi schema, tỷ lệ thiếu hoặc phân phối đầu vào thay đổi.

### Vòng đời model

- Registry tối thiểu cho artifact, feature schema, metric và approval.
- Quy trình rollback model độc lập với deploy giao diện.
- Shadow evaluation trước khi đổi model đang phục vụ.

## Điều kiện trước pilot thực tế

- Data contract và owner cho từng trường.
- Đánh giá calibration/subgroup trên dữ liệu địa phương đã được phê duyệt.
- Consent, kiểm soát truy cập, mã hóa, retention và audit.
- Theo dõi outcome sau hành động và quy trình nhân viên xử lý cảnh báo.
- Review riêng tư, bảo mật, pháp lý và an toàn lâm sàng.

Không tự động nhắn bệnh nhân hoặc retrain chỉ vì PSI tăng.

