# 🧭 DeFiSage

**AI-Powered DeFi Protocol Intelligence Platform** — Multi-agent risk, tokenomics, and governance analysis powered by Xiaomi MiMo.

![DeFiSage](https://img.shields.io/badge/AI-MiMo%20v2.5-blue)
![License](https://img.shields.io/badge/license-MIT-green)
![Tokens](https://img.shields.io/badge/daily%20tokens-5M%2B-orange)
![Stack](https://img.shields.io/badge/stack-FastAPI%20%2B%20Vanilla%20JS-purple)

## Overview

DeFiSage is a production-grade DeFi protocol intelligence platform that uses **four specialized AI agents** to produce institutional-quality research memos for live DeFi protocols. Built on top of Xiaomi MiMo's reasoning models, the platform turns a structured protocol snapshot into a Risk / Tokenomics / Governance / Investment Thesis stack — naturally consuming millions of API tokens per day for any team running continuous monitoring across the DeFi landscape.

Where most "AI audit" tools focus on Solidity bytecode, **DeFiSage analyzes live protocols**: TVL trajectory, oracle dependencies, custody posture, emission schedules, holder concentration, DAO health, and the cross-cutting risk that emerges from how those pieces interact.

## 🏗️ Architecture

```
┌────────────────────────────────────────────────────────────────────┐
│                            DeFiSage                                │
├────────────────────────────────────────────────────────────────────┤
│                                                                    │
│   ┌────────────┐  ┌────────────┐  ┌────────────┐  ┌────────────┐   │
│   │   Risk     │  │ Tokenomics │  │ Governance │  │  Thesis    │   │
│   │  Scanner   │  │  Auditor   │  │  Analyst   │  │ Composer   │   │
│   │ (Agent 1)  │  │ (Agent 2)  │  │ (Agent 3)  │  │ (Agent 4)  │   │
│   └─────┬──────┘  └─────┬──────┘  └─────┬──────┘  └─────┬──────┘   │
│         │               │               │               │          │
│         └───────────────┼───────────────┘               │          │
│                         │                               │          │
│                  ┌──────▼──────┐                 ┌──────▼──────┐   │
│                  │  Snapshot   │                 │  Synthesis  │   │
│                  │  Chunking   │                 │ + IR Memo   │   │
│                  └─────────────┘                 └─────────────┘   │
│                                                                    │
│   ┌──────────────────────────────────────────────────────────────┐ │
│   │            MiMo API (OpenAI-compatible inference)            │ │
│   │      Token Tracking · Daily Budget · Per-agent Telemetry     │ │
│   └──────────────────────────────────────────────────────────────┘ │
└────────────────────────────────────────────────────────────────────┘
```

## 🔥 Why It Consumes Millions of Tokens Daily

### 1. Multi-Agent Architecture
Each protocol intelligence run fans out to **4 specialized agents** in sequence:
- **Risk Scanner** — protocol/oracle/custody/bridge/centralization risk surface
- **Tokenomics Auditor** — emissions, vesting, holder concentration, unlock impact, treasury runway
- **Governance Analyst** — DAO posture, voter concentration, timelock effectiveness, multisig powers
- **Thesis Composer** — IR-grade memo with bull/bear/base case, sizing bands, kill-switch KPIs

### 2. Chunked Snapshot Analysis
Snapshots over 180 lines are split into overlapping chunks; each chunk is run through every relevant agent independently, then aggregated. A 600-line protocol snapshot easily fans out to 4 chunks × 3 specialists = 12 agent calls before synthesis.

### 3. Batch Processing
The batch endpoint analyzes up to 10 protocols in parallel with configurable concurrency — perfect for daily cross-protocol coverage at funds and research desks.

### 4. Interactive Research Copilot
The `/api/chat` endpoint exposes DeFiSage as a research assistant that answers protocol-level questions with rigor, consuming tokens on every interaction.

## Token Consumption Estimates

| Scenario | Protocols | Chunks | Agents | Tokens/Day |
|----------|-----------|--------|--------|-----------:|
| Single deep dive | 1 | 3-5 | 4 | ~80K |
| Daily research desk | 5 | 15-25 | 4 | ~450K |
| Multi-fund coverage | 15+ | 45+ | 4 | ~2M |
| Continuous monitoring + Q&A | 25+ | 75+ | 4 + chat | ~6M+ |

## 🚀 Quick Start

### 1. Backend (FastAPI)

```bash
cd backend
python -m venv .venv && source .venv/bin/activate
pip install -r requirements.txt
cp .env.example .env  # add your MiMo API key
uvicorn app.main:app --reload --port 8000
```

### 2. Frontend (Static)

```bash
cd frontend
python -m http.server 3000
# Open http://localhost:3000
```

For non-localhost hosts, the frontend uses same-origin `/api/*` requests — wire those to your backend via `netlify.toml` redirect (already prefilled), or set `window.DEFISAGE_API_BASE` before `app.js` loads.

### 3. Environment Variables

```env
MIMO_API_KEY=your_xiaomi_mimo_api_key
MIMO_BASE_URL=https://api.xiaomimimo.com/v1
MIMO_MODEL=mimo-v2.5-pro
DAILY_TOKEN_BUDGET=10000000
```

## 📡 API Endpoints

| Method | Endpoint | Description |
|--------|----------|-------------|
| POST | `/api/analyze` | Single protocol intelligence run |
| POST | `/api/batch-analyze` | Up to 10 protocols in parallel |
| POST | `/api/upload` | Upload `.md`/`.txt` snapshot file |
| POST | `/api/scaffold` | Get a snapshot scaffold to fill in |
| POST | `/api/chat` | Research copilot Q&A |
| GET  | `/api/stats` | Token usage statistics (daily) |
| GET  | `/api/stats/history` | Recent token usage entries |
| GET  | `/api/stats/trend` | 7-day daily token trend |
| GET  | `/api/agents` | List active agent roles |
| GET  | `/api/health` | Liveness + uptime |

## 📝 Snapshot Format

DeFiSage agents work best on a structured Markdown snapshot:

```md
# OVERVIEW
Name: Aave V3
Chain: Ethereum
Category: lending
Launch date: 2022-03

# TVL
Current: $9.4B
7d change: +1.2%
30d change: +6.8%
Peak TVL: $19B (2021-10)

# CONTRACTS
- Pool: 0x87870Bca3F3fD6335C3F4ce8392D69350B4fA4E2
- ACLManager: 0xc2aaCf6553D20d1e9d78E365AAba8032af9c85b0
- Treasury: 0x464C71f6c2F760DdA6093dCB91C24c39e5d6e18c

# TOKENOMICS
Total supply: 16,000,000 AAVE
Circulating: 14,830,000
Unlocks (next 90d): negligible
Emissions/day: from safety module
Top-10 holders share: 32%
Fee accrual: protocol → safety module + treasury

# GOVERNANCE
Voting venue: snapshot.org
Quorum: 320K AAVE
Timelock: 1 day short / 7 day long executor
Multisig signers: 6/9 Guardian
Upgrade pattern: Aave Governance v3, ACL-gated

# INCIDENTS
- 2023-11: CRV market frozen post-Curve exploit; recovery via swift governance
- Multiple post-mortems published
```

Use the **`Generate Scaffold`** button in the UI to drop in a starting template, or hit `POST /api/scaffold`.

## 🛠️ Tech Stack

- **AI Model**: Xiaomi MiMo v2.5 Pro (reasoning model)
- **Backend**: Python · FastAPI · OpenAI SDK · Async pipeline orchestration
- **Frontend**: Vanilla JS · CSS3 · Dark theme · Live token telemetry
- **API Protocol**: OpenAI-compatible (works with Claude Code, Cursor, OpenClaw, etc.)
- **Token Management**: Real-time tracking, budget enforcement, per-agent breakdown, persistent JSONL log

## 📊 Daily Token Budget

DeFiSage is designed to consume **5-10 million tokens daily** through:

1. **Continuous protocol monitoring** — refreshing snapshots and re-running analysis as TVL / unlocks / governance state evolve
2. **Batch coverage** — parallel analysis across the long tail of protocols a fund tracks
3. **Deep multi-agent pipeline** — 4 agents × multiple chunks per protocol
4. **Interactive research Q&A** — analysts pinging the copilot all day
5. **Memo generation** — IR-grade synthesis output for portfolio reviews

## 🧪 Example: Run an Analysis from cURL

```bash
curl -X POST http://localhost:8000/api/analyze \
  -H "Content-Type: application/json" \
  -d '{
    "protocol_name": "GMX V2",
    "chain": "Arbitrum",
    "snapshot": "# OVERVIEW\nName: GMX V2\nChain: Arbitrum\n# TVL\nCurrent: $480M\n..."
  }'
```

## 📜 License

MIT — see [LICENSE](./LICENSE).

## 🙏 Built with Xiaomi MiMo

DeFiSage is part of the **Xiaomi MiMo Orbit 100T Token Creator Incentive Program**. Find out more at [platform.xiaomimimo.com](https://platform.xiaomimimo.com).
