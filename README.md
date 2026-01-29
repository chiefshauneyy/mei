# MEI — Modular Executive Intelligence

Local-first personal agent system running on a MacBook home server.

## Goals (Phase 1)
- Core runner that executes agents
- Agents can send notifications via ntfy
- No secrets committed to git

## Structure
- core/    — orchestrator
- agents/  — modular agents
- config/  — configs and secrets
- logs/    — logs
- data/    — cached state

## Quick start
export NTFY_TOPIC="mei-alerts"
python3 core/mei_core.py
