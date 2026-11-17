# Kiến trúc hệ thống

## Thành phần

```text
                 ┌──────────────────────┐
                 │ Synthetic generator  │
                 └──────────┬───────────┘
                            v
       ┌──────────── data quality gates ────────────┐
       │                                            │
       v                                            v
 raw/appointments.csv                    processed SQLite + CSV
                                                    │
                                      time-based train/val/test
                                                    │
                                                    v
                                      preprocessing + model
                                         │             │
                                         v             v
                                    model bundle   metrics/card
                                         │
                     ┌───────────────────┼──────────────────┐
                     v                   v                  v
               online API          batch scoring       monitoring
                     │                                      │
                     v                                      v
               Vietnamese UI                      PSI + review rate
```

## Quyết định triển khai

- `run_pipeline.py` là entrypoint tái lập dữ liệu, SQLite, model và reports.
- Preprocessing nằm trong `sklearn.Pipeline` để train và inference dùng đúng một logic.
- Bundle chứa model version, schema version, threshold và score distribution tham chiếu.
- FastAPI phục vụ cả API và static frontend, nên ứng dụng chỉ cần một service.
- Batch và online cùng đọc một bundle; không có hai phiên bản logic chấm điểm.
- Health endpoint trả readiness cùng model version để đối chiếu khi vận hành.

## Ranh giới an toàn

- Không sử dụng dữ liệu bệnh nhân thật.
- Target là việc đến hẹn, không phải kết quả lâm sàng.
- Output chỉ tạo hàng đợi xem xét; không có hành động tự động.
- Tách dữ liệu theo thời gian để giảm leakage.
- Monitoring cảnh báo nhưng không tự động retrain.

## Hướng production hóa

Prototype chưa có authentication, authorization, audit database, secrets manager, encrypted storage, model registry độc lập, canary release và monitoring outcome sau hành động. Đây là các control bắt buộc phải thiết kế với chủ hệ thống trước pilot thực tế.
