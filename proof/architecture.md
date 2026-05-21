# DeFiSage Multi-Agent Architecture

## Pipeline

```
User input (DeFi protocol snapshot, ~3-8K tokens)
        |
        v
+----------------------------+
| 1. Risk Scanner Agent      |  <- MiMo reasoning, ~12K tokens
|    - TVL volatility        |
|    - Oracle dependency     |
|    - Exploit pattern match |
+----------------------------+
        |
        v
+----------------------------+
| 2. Tokenomics Auditor      |  <- MiMo reasoning, ~10K tokens
|    - Emission schedule     |
|    - Holder distribution   |
|    - Vesting / unlock risk |
+----------------------------+
        |
        v
+----------------------------+
| 3. Governance Analyst      |  <- MiMo reasoning, ~8K tokens
|    - DAO health metrics    |
|    - Proposal risk vector  |
+----------------------------+
        |
        v
+----------------------------+
| 4. Thesis Composer         |  <- MiMo reasoning, ~15K tokens
|    - IR-quality memo       |
|    - Investment scoring    |
+----------------------------+
        |
        v
Final structured report (Markdown)

Plus:
- 5. Copilot Chat: stateful Q&A on completed reports (~2-5K tokens / turn)
```

## Token consumption per analysis run

- Avg single-protocol pipeline: ~45-50K tokens
- Multi-protocol batch (10 protocols): ~500K tokens
- Continuous fund monitoring (50 protocols/day, 2x cycle): ~5M tokens/day
- Copilot chat throughput: ~30K tokens / active session

## Stack

- Backend: FastAPI (Python 3.11), httpx async, Pydantic v2
- Frontend: vanilla JS, no framework
- Token tracker: JSONL audit log, daily budget enforcement
- Deployment: Netlify (frontend) + Render/Railway (backend, planned)
