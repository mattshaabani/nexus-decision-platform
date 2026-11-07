# Model risk management summary

## Champion and challenger
A challenger model may replace the champion only if the quality gate passes, including
minimum Gini uplift versus the current champion and fairness floors.

## Monitoring
Production scores are compared to the training baseline using PSI and calibration metrics.
Retrain is recommended when policy triggers fire; promotion still requires a full gate.

## Support tools
LLM-based support may explain decisions and retrieve policy. It must not approve, decline,
or promote models.