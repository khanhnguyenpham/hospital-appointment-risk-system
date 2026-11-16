# Architecture

```text
Synthetic generator
       |
       v
raw CSV -- validation/cleaning --> processed CSV --> SQLite --> dashboard / SQL
                                      |
                                      v
                              feature pipeline
                                      |
                                      v
                        logistic regression model
                               |             |
                               v             v
                         evaluation JSON   FastAPI
```

## Design boundaries

- No real patient information is used.
- The target is appointment attendance, not a clinical outcome.
- Predictions are a prioritization signal for staff, not an automated action.
- Training and test data are split by time to reduce leakage from the future.

