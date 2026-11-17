# Dữ liệu

- `raw/appointments.csv`: nguồn tổng hợp do generator tạo.
- `processed/appointments_clean.csv`: dữ liệu đã qua quality gates.
- `processed/hospital_operations.db`: SQLite gồm bảng lịch hẹn và khoa.

Các file sinh ra không commit vào Git vì có thể tái lập bằng:

```bash
python run_pipeline.py
```

Generator dùng seed 42. ID bệnh nhân là chuỗi băm giả lập và không đại diện cá nhân thật.
