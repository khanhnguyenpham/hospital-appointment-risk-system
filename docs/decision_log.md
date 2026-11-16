# Decision log

## Why synthetic data?

Real patient and appointment data are sensitive. A reproducible generator lets me demonstrate data engineering and analysis without implying access to confidential hospital records.

## Why a time-based split?

A random split can put future appointments into training and older appointments into testing. I use the oldest 70% for training, the next 15% for validation and the newest 15% for testing.

## Why logistic regression?

The project needs a reliable baseline and understandable probabilities. A more complex model may improve ranking, but it should only replace this baseline after measuring the trade-off between performance and explainability.

## Why no automated reminders?

The project only ranks appointments. Sending messages would require consent, workflow ownership and monitoring. Keeping a human review step is the safer design for a portfolio prototype.

