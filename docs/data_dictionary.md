# Data dictionary

| Column | Type | Description |
|---|---|---|
| appointment_id | string | Unique appointment identifier |
| patient_id | string | Synthetic hashed patient identifier |
| appointment_date | date | Scheduled visit date |
| booked_at | datetime | Time the appointment was created |
| department | category | Outpatient department |
| appointment_hour | integer | Scheduled hour from 7 to 16 |
| age_group | category | Coarse age band, not exact age |
| district | category | Broad residence area |
| insurance_type | category | Public, Private or Self-pay |
| prior_visits | integer | Number of earlier visits in the synthetic history |
| prior_no_shows | integer | Number of earlier missed appointments |
| reminder_sent | boolean | Whether a reminder was recorded |
| status | category | Completed, No-show or Cancelled |
| arrival_time | datetime | Arrival time when the patient attended |
| service_start_time | datetime | Time service started |
| wait_minutes | float | Minutes between arrival and service start |
| consultation_minutes | float | Simulated consultation duration |
| no_show | boolean | Modelling target; 1 when status is No-show |
| lead_days | integer | Days between booking and appointment |
| weekday | integer | Monday=0, Sunday=6 |
| month | integer | Calendar month |

