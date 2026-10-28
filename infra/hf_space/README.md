---
title: OrchardIQ Enterprise Lakehouse Backend
emoji: 🍏
colorFrom: green
colorTo: gray
sdk: docker
app_port: 8000
pinned: false
license: mit
---

# OrchardIQ Backend on Hugging Face Spaces

This repository contains the containerized FastAPI backend for OrchardIQ.

### Environment Secrets:
- `DEMO_MODE`: `true`
- `MOCK_LLM_MODE`: `true`
- `PER_IP_RATE_LIMIT_PER_MINUTE`: `60`
- `DAILY_COST_CAP_USD`: `10.0`
- `ANTHROPIC_API_KEY`: (Optional) Your Anthropic Claude API Key

### API Endpoints:
- `GET /health`: Platform health check
- `POST /ask`: Multi-agent Lakehouse reasoning (SSE stream or JSON)
- `GET /catalog/tables`: Star-schema data catalog
- `GET /quality/report`: Data quality gate checks
- `GET /audit/records`: Immutable cryptographic audit trail
