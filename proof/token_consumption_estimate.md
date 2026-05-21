# Daily Token Consumption — Projected

| Workload | Per run | Frequency | Daily total |
|---|---|---|---|
| Single-protocol full audit | 50K | 30 / day | 1.5M |
| Batch monitoring (50 protocols) | 2.5M | 2 / day | 5.0M |
| Copilot chat sessions | 30K | 100 sessions | 3.0M |
| Scaffold generation | 5K | 200 / day | 1.0M |
| **Estimated daily total** | | | **10.5M tokens** |

## Why DeFiSage burns tokens by design

- Multi-stage pipeline: 4 sequential agents per snapshot, no caching between agents
- Long context: protocol snapshots include docs, governance forum threads, on-chain stats
- Reasoning depth: each agent runs full chain-of-thought on its specialized domain
- Continuous monitoring: same protocol re-analyzed daily as on-chain state changes
