Dependency Map

api/v1/               →  schemas/  +  pipeline/
pipeline/stages/      →  core/     +  instruments/
core/financial/       →  config/
core/period/          →  config/
instruments/          →  config/   +  core/financial/
middleware/           →  config/   +  observability/
observability/        →  config/

Rule: No circular deps. Lower layers never import upper layers.
api → pipeline → core → config (one direction only)

------------------------------------------------------------------------------------------
------------------------------------------------------------------------------------------

DEPENDENCY LAYER VISUALIZATION

┌─────────────────────────────────────┐
│           API Layer                 │  ← HTTP only, thin
│     api/v1/  +  schemas/            │
└──────────────┬──────────────────────┘
               ↓
┌─────────────────────────────────────┐
│         Pipeline Layer              │  ← Orchestration only
│   pipeline/orchestrator.py          │
│   pipeline/stages/s1 → s6           │
└──────────────┬──────────────────────┘
               ↓
┌─────────────────────────────────────┐
│           Core Layer                │  ← Pure business logic
│  core/financial/  core/period/      │
│  core/validation/ instruments/      │
└──────────────┬──────────────────────┘
               ↓
┌─────────────────────────────────────┐
│         Config Layer                │  ← No business logic
│   config/settings.py                │
│   config/tax_slabs.py               │
└─────────────────────────────────────┘

Cross-cutting (never in above stack):
┌─────────────────────────────────────┐
│       Middleware + Observability    │
│  timing, rate_limiter, metrics,     │
│  logging, tracing                   │
└─────────────────────────────────────┘