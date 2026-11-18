# Hệ thống ưu tiên nhắc lịch ngoại trú

[![CI](https://github.com/khanhnguyenpham/hospital-appointment-risk-system/actions/workflows/ci.yml/badge.svg)](https://github.com/khanhnguyenpham/hospital-appointment-risk-system/actions/workflows/ci.yml)

Project AI Systems tập trung vào một bài toán vận hành có ranh giới rõ: **xếp hạng lịch hẹn ngoại trú để nhân viên ưu tiên nhắc lịch**. Đây không phải notebook trình diễn. Repository có pipeline dữ liệu, quality gates, mô hình có baseline, API online/batch, theo dõi drift, giao diện web và tài liệu quản trị mô hình.

> 100% dữ liệu là dữ liệu tổng hợp. Project không liên kết với Bệnh viện Thiện Hạnh hay bất kỳ cơ sở y tế cụ thể nào; không chẩn đoán và không tự động từ chối, hủy hoặc dời lịch khám.

## Vị trí trong portfolio

Đây là project tổng hợp phần tôi quan tâm nhất: đưa một mô hình từ pipeline dữ liệu sang API, giao diện, kiểm thử và monitoring có ranh giới sử dụng rõ ràng. Nền tảng phân tích và KPI nằm trong [project Data Analyst](https://github.com/khanhnguyenpham/outpatient-operations-analysis); phần transaction và nghiệp vụ backend nằm trong [Kho Gọn](https://github.com/khanhnguyenpham/inventory-order-management).

Xem [lịch phát triển](CHANGELOG.md), [roadmap](ROADMAP.md) và [hành trình học tập 2022–2026](https://github.com/khanhnguyenpham).

## Dùng trực tuyến

- Ứng dụng: [https://appointment-risk-system.onrender.com](https://appointment-risk-system.onrender.com)
- OpenAPI: [https://appointment-risk-system.onrender.com/docs](https://appointment-risk-system.onrender.com/docs)
- Health check: [https://appointment-risk-system.onrender.com/health](https://appointment-risk-system.onrender.com/health)

Render Free có thể tạm dừng dịch vụ khi không có truy cập; lần mở đầu tiên đôi khi cần chờ khoảng 30–60 giây.

## Vì sao tôi làm project này

Tôi muốn chứng minh khả năng nối các phần thường bị tách rời trong một bài ML: dữ liệu đầu vào, đánh giá trung thực, giới hạn vận hành, phục vụ mô hình và giám sát sau triển khai. Câu hỏi chính không chỉ là “mô hình chính xác bao nhiêu” mà còn là:

- dữ liệu có đúng schema và không bị leakage hay không;
- mô hình có tốt hơn baseline đơn giản hay không;
- đội vận hành có xử lý nổi số lịch bị gắn cờ hay không;
- khi phân phối đầu vào thay đổi thì ai được cảnh báo;
- điểm số được phép và không được phép dùng vào việc gì.

## Luồng hệ thống

```text
Synthetic generator ──> validation ──> CSV + SQLite
                              │
                              v
                   chronological split
                    train / val / test
                              │
                              v
           preprocessing + logistic regression
                    │                    │
                    v                    v
             model bundle          model card
                    │
          ┌─────────┴──────────┐
          v                    v
    FastAPI online       batch scoring
          │
          ├── ứng dụng web
          └── PSI monitoring + review rate
```

Chi tiết hơn tại [docs/architecture.md](docs/architecture.md).

## Kết quả tham chiếu

Pipeline sử dụng seed 42 và chia theo thời gian: 70% train, 15% validation, 15% test. Ngưỡng được chọn trên validation với ràng buộc tối đa 30% lịch hẹn đi vào hàng đợi xem xét.

| Chỉ số trên test | Logistic regression | Baseline theo tỷ lệ lớp |
|---|---:|---:|
| ROC–AUC | 0.678 | 0.500 |
| Brier score ↓ | 0.152 | 0.163 |
| Expected calibration error ↓ | 0.0288 | 0.0260 |
| Precision | 0.347 | 0.000 |
| Recall | 0.517 | 0.000 |
| F1 | 0.415 | 0.000 |
| Tỷ lệ đưa vào review | 30.4% | 0.0% |

ROC–AUC cho thấy mô hình xếp hạng tốt hơn ngẫu nhiên, nhưng Brier score và Expected Calibration Error chưa vượt baseline tỷ lệ lớp. Tôi giữ kết quả này vì nó phản ánh đúng trade-off: mô hình có ích để tạo hàng đợi ưu tiên, chưa đủ để coi xác suất là dự báo đã hiệu chỉnh hoàn hảo. Xem đầy đủ tại [docs/model_card.md](docs/model_card.md).

## Chạy project

Yêu cầu Python 3.11–3.13.

```bash
python -m venv .venv
# Windows
.venv\Scripts\activate
# macOS/Linux: source .venv/bin/activate

pip install -r requirements.txt
python run_pipeline.py
uvicorn api:app --reload
```

Mở:

- ứng dụng web: `http://127.0.0.1:8000`
- OpenAPI: `http://127.0.0.1:8000/docs`
- health check: `http://127.0.0.1:8000/health`

Dashboard Streamlit cho phân tích nội bộ là phần tùy chọn:

```bash
pip install -r requirements-dashboard.txt
streamlit run app.py
```

## API chính

| Method | Endpoint | Mục đích |
|---|---|---|
| `GET` | `/health` | readiness và phiên bản model |
| `GET` | `/metadata` | metrics, threshold, subgroup evaluation |
| `GET` | `/analytics/summary` | số liệu tổng hợp cho dashboard |
| `POST` | `/predict` | chấm một lịch hẹn + yếu tố tác động |
| `POST` | `/predict-batch` | chấm tối đa 500 lịch mỗi request |
| `POST` | `/monitor` | PSI, review rate và trạng thái drift |
| `GET` | `/monitor/scenario` | hai kịch bản monitoring tái lập để kiểm tra hệ thống |

Ví dụ:

```bash
curl -X POST http://127.0.0.1:8000/predict \
  -H "Content-Type: application/json" \
  -d '{
    "department": "Cardiology",
    "appointment_hour": 8,
    "weekday": 0,
    "month": 9,
    "lead_days": 18,
    "prior_visits": 3,
    "prior_no_shows": 2,
    "reminder_sent": 0,
    "age_group": "45-64",
    "district": "Outside Buon Ma Thuot",
    "insurance_type": "Public"
  }'
```

Schema dùng enum và range validation; lịch sử bỏ hẹn không thể lớn hơn tổng số lần khám trước.

## Batch scoring

```bash
python batch_score.py scheduled_appointments.csv scored_appointments.csv
```

File đầu ra được xếp giảm dần theo xác suất để phục vụ **review thủ công**. Online API và batch job dùng cùng một model bundle, preprocessing và threshold.

## Monitoring

Endpoint `/monitor` so sánh phân phối điểm của batch mới với phân phối train bằng Population Stability Index (PSI):

- `< 0.10`: ổn định;
- `0.10–0.25`: cần theo dõi;
- `>= 0.25`: cần điều tra.

PSI chỉ là tín hiệu. Hệ thống không tự động retrain. Khi cảnh báo xuất hiện, quy trình đúng là kiểm tra schema, chất lượng dữ liệu, thay đổi nghiệp vụ và hiệu năng có nhãn trước.

## Cấu trúc repository

```text
├── api.py                         # FastAPI + public web
├── app.py                         # Streamlit analyst dashboard
├── batch_score.py                 # chấm điểm file
├── run_pipeline.py                # pipeline một lệnh
├── web/                           # giao diện tiếng Việt
├── src/hospital_analytics/        # data, feature, train, monitor
├── tests/                         # quality, API, drift, split tests
├── sql/analysis_queries.sql       # truy vấn vận hành
├── docs/                          # kiến trúc, model card, decisions
├── Dockerfile
└── render.yaml
```

## Kiểm thử và container

```bash
ruff check .
pytest
docker build -t appointment-risk-system .
docker run --rm -p 8000:8000 appointment-risk-system
```

CI chạy lint, test, pipeline tái lập và kiểm tra khởi động API trên Python 3.12.

## Nếu có dữ liệu thật

Trước pilot cần thống nhất định nghĩa bỏ hẹn, consent và thời điểm nhắc; đánh giá calibration và subgroup trên dữ liệu địa phương; kiểm soát truy cập, audit log, mã hóa, retention; theo dõi outcome sau hành động; và có phê duyệt riêng tư, bảo mật, pháp lý, an toàn lâm sàng. Những việc này không thể được “giả lập là đã xong” trong một portfolio project.

## Tác giả

Nguyễn Phạm Đức Khánh · Sinh viên Khoa học máy tính, quan tâm Data Analytics và AI Systems.
