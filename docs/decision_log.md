# Nhật ký quyết định

## Vì sao dùng dữ liệu tổng hợp?

Lịch sử bệnh nhân và lịch khám là dữ liệu nhạy cảm. Generator có seed cố định cho phép minh họa data engineering và ML mà không ngụ ý tôi có quyền truy cập dữ liệu của bệnh viện thật.

## Vì sao chia theo thời gian?

Random split có thể đưa lịch hẹn tương lai vào train và lịch cũ vào test. Project dùng 70% bản ghi cũ nhất cho train, 15% tiếp theo cho validation và 15% mới nhất cho test.

## Vì sao logistic regression?

Đây là baseline dễ kiểm tra, chạy nhanh và có thể phân tích contribution theo từng dự đoán. Model phức tạp chỉ nên thay thế khi cải thiện có ý nghĩa trên dữ liệu thật và trade-off về calibration, latency, giải thích được chấp nhận.

## Vì sao threshold không chỉ tối ưu F1?

Một đội nhắc lịch có năng lực hữu hạn. Project tìm threshold có F1 tốt trong các ngưỡng mà tỷ lệ review trên validation không vượt 30%. Con số 30% là giả định vận hành có ghi rõ, không phải sự thật về bệnh viện nào.

## Vì sao không tự động gửi nhắc lịch?

Gửi tin cần consent, ownership, template được duyệt, giới hạn tần suất, xử lý opt-out và audit. Prototype chỉ xếp hạng; nhân viên vẫn quyết định hành động.

## Vì sao giữ kết quả calibration chưa hơn baseline?

Brier score của logistic regression gần nhưng chưa tốt hơn baseline tỷ lệ lớp. Xóa chi tiết này sẽ làm project trông đẹp hơn nhưng thiếu trung thực. Model hiện phù hợp để thử nghiệm **ranking queue**, chưa đủ cơ sở để tuyên bố xác suất production-ready.

## Vì sao PSI không tự động retrain?

Score drift có thể do mùa vụ, thay đổi quy trình, lỗi dữ liệu hoặc thay đổi thật trong quần thể. Retrain tự động có thể hấp thụ lỗi. Cảnh báo phải dẫn tới điều tra và đánh giá có nhãn trước.
