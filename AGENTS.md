# AGENTS.md — Multi-Agent Collaboration Protocol
**Lodge-Link Development Team**

This document defines how multiple AI agents (and human developers) work on this codebase simultaneously without logical conflicts.

---

## The Golden Rule
**The `docs/Lodge-Link_Implementation_Plan.md` is the constitution. `PHASE_STATUS.json` is the law. `FEATURE_LOCKS.json` is the traffic controller.**

When in doubt, a feature's behavior is whatever the Implementation Plan says it should be, scoped to the active phase.

---

## Agent Identity
Each agent session must have a unique `agent_id`. Use the format: `{name}-{machine}`.
Examples: `claude-fatima-laptop`, `claude-abel-desktop`, `claude-dev-1`

This ID goes in `FEATURE_LOCKS.json` when you claim a feature.

---

## The Feature Claim Protocol (Mandatory)

### Step 1 — Before touching any code
```bash
# Read current phase
cat PHASE_STATUS.json

# Read available features for current phase
cat FEATURE_LOCKS.json
```

### Step 2 — Claim your feature
Create a tiny PR that ONLY updates `FEATURE_LOCKS.json`:
```json
"backend_referral_fanout": {
  "status": "claimed",
  "agent_id": "claude-abel-desktop",
  "branch": "phase1/referral-fanout",
  "claimed_at": "2025-01-15T09:00:00Z",
  "released_at": null
}
```

### Step 3 — Build the feature on your branch
Branch: `phase1/{feature-name}`

### Step 4 — Release the claim on merge
When your PR merges to `develop`, update the entry:
```json
"status": "released",
"released_at": "2025-01-18T14:30:00Z"
```

---

## Conflict Prevention Rules

| Scenario | Rule |
|---|---|
| Two agents want the same feature | First to have a merged claim PR wins. Second agent picks another available feature. |
| Agent is blocked waiting for another feature | Check if any other `"available"` feature unblocks you. If genuinely blocked, flag in PR comments — don't build the dependency yourself without claiming it. |
| Feature has no owner and is urgently needed | Team lead can force-claim it in `FEATURE_LOCKS.json` directly to `main`. |
| Agent gets abandoned mid-feature | After 48h of no commit activity on a claimed feature, the claim can be revoked by team lead. |

---

## Module Ownership (Default Assignment Guidance)

These are suggestions, not locks. Check `FEATURE_LOCKS.json` for actual claims.

| Module | Suggested Team |
|---|---|
| Backend API + Database | Backend agents |
| Frontend PWA + i18n | Frontend agents |
| Celery workers + SMS | Backend agents |
| Docker / CI / Infrastructure | DevOps lead |
| CLAUDE.md / AGENTS.md / Docs | Team lead only |

---

## Shared State — What Everyone Must Read Every Session
1. `CLAUDE.md` — always (auto-read by Claude Code)
2. `PHASE_STATUS.json` — before starting work
3. `FEATURE_LOCKS.json` — before claiming or building anything
4. The relevant section of `docs/Lodge-Link_Implementation_Plan.md`

---

## What Happens When Phase 1 Is Done?
A human team lead reviews all Phase 1 exit criteria (defined in `docs/phases/PHASE_1_MVP.md`).
If all boxes are checked, they update `PHASE_STATUS.json`:
```json
"1": { "status": "completed", "completed_at": "2025-05-01T00:00:00Z" },
"2": { "status": "in_progress", "unlocked_at": "2025-05-01T00:00:00Z" }
"current_phase": 2
```
Agents automatically operate under Phase 2 rules from that point forward.
