# Operations Runbook

This document contains the operational procedures for verifying service status and managing runtime components.

## Service Startup and Health Checks

After starting services, verify connectivity to the health-check endpoints for both `embed-llm` and `agent-llm`.

```bash
bash deploy/setup_services.sh

curl -s http://127.0.0.1:8081/health   # embed-llm
curl -s http://127.0.0.1:8080/health   # agent-llm

bash deploy/start_agent.sh
```
