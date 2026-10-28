# Statistical Anomaly Detection Thresholds

## Monitored Metrics
- **Claims Frequency**: Anomaly flagged if weekly claims per product exceed $\mu + 3\sigma$.
- **Return Rate**: Anomaly flagged if weekly return percentage exceeds $4.0\%$.
- **Revenue Volatility**: Anomaly flagged if period-over-period variance exceeds $\pm 25\%$ without a registered holiday or launch event.
