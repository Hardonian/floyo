# Optimization Plan

- **perf** — Edge runtime for light APIs → set runtime="edge" where safe _(impact: latency↓)_
- **security** — Validate inputs & typed JSON → zod/yup guards _(impact: risk↓)_
- **db** — Split CONCURRENT indexes from TX → standalone online-safe migrations _(impact: locks↓)_
- **ux** — Route-level code-splitting → dynamic imports _(impact: LCP↓)_
