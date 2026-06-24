# Event Bus: System Overview

## Purpose

The Event Bus provides an internal publish/subscribe backbone for the LLM agent system. Producers publish JSON events; consumers subscribe to topics via SSE and replay past events.

## Security model

The Event Bus API has **no authentication or ACL**.

- **Design assumption**: single-node deployment on an internal network / trusted hosts
- **Access control**: enforced at the network boundary (firewall, Docker network)
- **Do not expose publicly**: the Event Bus must not be directly reachable from the internet

### Future authentication options

If requirements arise:
- API-key authentication via FastAPI `Depends`
- mTLS for service-to-service authentication

Not implemented at this time. Evaluate based on the actual threat model before adding.
