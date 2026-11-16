# Data folders

- `raw/appointments.csv`: synthetic source file created by the generator.
- `processed/appointments_clean.csv`: validated and feature-ready data.
- `processed/hospital_operations.db`: SQLite database with appointment and department tables.

Generated files are excluded from Git because they can be reproduced with:

```bash
python run_pipeline.py
```

