---
title: "Memory Layer — Module Reference"
category: agent
tags:
  - agent
  - agent
  - memory
  - semantic
  - episodic
  - embedding
related:
  - 05_agent_00_document-guide.md
---

# Memory Layer — Module Reference

erview

Persistent Semantic Memory stores abstract rules, design decisions, failure patterns,
and conversational Q&A across agent sessions.

**Memory types**:
- Semantic: long-lived rules and decisions (importance ≥ 0.5 for session startup injection)
- Episodic: session-specific failures and Q&A (injected on first user prompt)

**Source types**: RULE / DECISION / FAILURE / CONVERSATION

**Local-only guarantee**: set `memory_local_only = true` to enforce that the embedding
endpoint is a loopback address. Fails startup if `embed_url` is non-local.

**Automatic context restoration**:
- Session start: pinned + high-importance semantic injected
- First user prompt: task-specific hybrid retrieval (semantic + episodic)

## Production Checklist

- [ ] `me

mory_local_only = true` if data must not leave the machine
- [ ] `embed_url` points to local embedding service (e.g., `http://localhost:11434`)
- [ ] `/memory status` shows one of: `Hybrid mode`, `FTS-only`, `Degraded mode`, or `disabled`
- [ ] `/memory rebuild` tested after restoring JSONL backup

---

## Purpose

API reference for all 

modules under `scripts/agent/memory/`. A developer should
understand each module's responsibility, public API surface, and disabled behavior
without reading source code.

---

## Overview

| Module | Responsibi

## Related Documents

- `agent`
- `memory`
- `semantic`

## Keywords

agent
memory
semantic
episodic
embedding
