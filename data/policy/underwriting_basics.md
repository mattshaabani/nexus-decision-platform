# Underwriting basics

## Credit utilisation
Higher revolving utilisation is associated with higher default risk.
Applications with utilisation above 70% typically receive stronger adverse reason codes.

## Income
Higher documented income generally supports lower risk scores, all else equal.
Income is evaluated with monotonic WoE bins; very low income bins contribute more to decline.

## Age
Age is used only as a risk factor within legal bounds. Extremely young applicants may show thinner files.

## Decision outcomes
Approve means predicted risk is below the configured probability threshold.
Decline means predicted risk is at or above the threshold.
Reason codes list the top features that most increased predicted risk for this application.
Support staff must not override model outcomes without a logged human override.