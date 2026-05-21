"""Multi-Agent DeFi Protocol Intelligence Pipeline.

Orchestrates four specialized AI agents to perform a deep analysis of a DeFi
protocol snapshot. Each agent runs against multiple chunked sections of the
snapshot to maximize coverage, naturally consuming significant API tokens.

Pipeline stages:
1. Preprocessing — slice the snapshot into overlapping sections (TVL, contracts,
   tokenomics, governance, incidents) for chunked analysis.
2. Risk Scan — agent surfaces protocol/oracle/custody risks per section.
3. Tokenomics Audit — agent evaluates emissions, holders, unlocks per section.
4. Governance Analysis — agent assesses DAO posture per section.
5. Thesis Synthesis — final agent composes the institutional memo from all
   prior outputs.
"""

from __future__ import annotations

import asyncio
import time
import uuid

from app.core.config import settings
from app.core.token_tracker import TokenTracker
from app.services.mimo_client import MiMoClient


class ProtocolAnalysisPipeline:
    """Orchestrates multi-agent DeFi protocol analysis."""

    AGENTS = [
        {"id": "risk", "role": "risk_scanner", "priority": 1},
        {"id": "tokenomics", "role": "tokenomics_auditor", "priority": 2},
        {"id": "governance", "role": "governance_analyst", "priority": 2},
        {"id": "thesis", "role": "thesis_composer", "priority": 3},
    ]

    def __init__(self, mimo_client: MiMoClient, token_tracker: TokenTracker):
        self.client = mimo_client
        self.tracker = token_tracker

    def _chunk_snapshot(
        self,
        snapshot: str,
        chunk_size: int | None = None,
        overlap: int | None = None,
    ) -> list[str]:
        """Split a structured protocol snapshot into overlapping chunks."""
        chunk_size = chunk_size or settings.PROTOCOL_CHUNK_SIZE
        overlap = overlap or settings.PROTOCOL_CHUNK_OVERLAP
        lines = snapshot.split("\n")
        if not lines:
            return [snapshot]
        chunks: list[str] = []
        i = 0
        while i < len(lines):
            end = min(i + chunk_size, len(lines))
            chunk = "\n".join(lines[i:end])
            if chunk.strip():
                chunks.append(chunk)
            i += max(1, chunk_size - overlap)
        return chunks or [snapshot]

    def _estimate_complexity(self, snapshot: str) -> dict:
        """Estimate snapshot complexity for resource budgeting."""
        lines = snapshot.split("\n")
        loc = len([l for l in lines if l.strip() and not l.strip().startswith("#")])

        signals = {
            "addresses": snapshot.count("0x") - snapshot.count("0x0000000000000000000000000000000000000000"),
            "chains_mentioned": sum(
                1
                for chain in (
                    "Ethereum",
                    "Arbitrum",
                    "Base",
                    "Optimism",
                    "Polygon",
                    "Avalanche",
                    "BNB",
                    "Solana",
                    "Sui",
                    "Aptos",
                    "Mantle",
                    "Linea",
                    "Scroll",
                    "Berachain",
                )
                if chain.lower() in snapshot.lower()
            ),
            "oracles_mentioned": sum(
                1
                for o in ("Chainlink", "Pyth", "RedStone", "API3", "TWAP", "Uniswap V3")
                if o.lower() in snapshot.lower()
            ),
            "incidents_mentioned": sum(
                1
                for k in ("exploit", "hack", "drain", "rug", "post-mortem", "incident")
                if k in snapshot.lower()
            ),
            "governance_signals": sum(
                1 for k in ("snapshot", "tally", "timelock", "multisig", "veto", "proposal") if k in snapshot.lower()
            ),
            "tokenomics_signals": sum(
                1
                for k in ("emission", "vest", "unlock", "circulating", "fdv", "treasury", "buyback")
                if k in snapshot.lower()
            ),
        }

        complexity_score = (
            loc * 0.05
            + signals["addresses"] * 1.2
            + signals["chains_mentioned"] * 4
            + signals["oracles_mentioned"] * 5
            + signals["incidents_mentioned"] * 6
            + signals["governance_signals"] * 3
            + signals["tokenomics_signals"] * 3
        )

        if complexity_score < 25:
            level = "low"
        elif complexity_score < 70:
            level = "medium"
        elif complexity_score < 130:
            level = "high"
        else:
            level = "critical"

        return {
            "score": round(complexity_score, 1),
            "level": level,
            "loc": loc,
            "signals": signals,
            "expected_chunks": max(1, loc // settings.PROTOCOL_CHUNK_SIZE),
        }

    async def run_agent(
        self,
        agent_role: str,
        snapshot: str,
        context: str = "",
        analysis_id: str = "",
    ) -> dict:
        """Run a single analysis agent."""
        result = await self.client.analyze_protocol(
            snapshot=snapshot,
            agent_role=agent_role,
            context=context,
            temperature=settings.AGENT_TEMPERATURE,
            max_tokens=settings.AGENT_MAX_TOKENS,
        )
        tokens = result.get("tokens", {}).get("total", 0)
        self.tracker.record_usage(tokens, agent=agent_role, analysis_id=analysis_id)
        return {
            "agent": agent_role,
            "result": result.get("content", "") or "",
            "tokens_used": tokens,
            "elapsed": result.get("elapsed_seconds", 0),
            "error": result.get("error"),
        }

    async def _run_chunked_agent(
        self,
        agent: dict,
        chunks: list[str],
        protocol_name: str,
        complexity: dict,
        analysis_id: str,
    ) -> dict:
        """Run one agent across all chunks then return aggregated result."""
        if len(chunks) == 1:
            single = await self.run_agent(agent["role"], chunks[0], "", analysis_id)
            single["chunks_analyzed"] = 1
            return single

        chunk_results: list[dict] = []
        for i, chunk in enumerate(chunks):
            context = (
                f"Chunk {i + 1}/{len(chunks)} of {protocol_name} "
                f"(complexity={complexity['level']}, total LoC={complexity['loc']})"
            )
            chunk_results.append(
                await self.run_agent(agent["role"], chunk, context, analysis_id)
            )

        combined = "\n\n---\n\n".join(r["result"] for r in chunk_results if r.get("result"))
        return {
            "agent": agent["role"],
            "result": combined,
            "tokens_used": sum(r["tokens_used"] for r in chunk_results),
            "elapsed": sum(r["elapsed"] for r in chunk_results),
            "chunks_analyzed": len(chunks),
        }

    async def analyze(
        self,
        snapshot: str,
        protocol_name: str = "Unknown Protocol",
        run_governance: bool = True,
    ) -> dict:
        """Run the full multi-agent analysis pipeline against a protocol snapshot."""
        analysis_id = str(uuid.uuid4())[:8]
        start_time = time.time()

        complexity = self._estimate_complexity(snapshot)
        chunks = self._chunk_snapshot(snapshot)

        # Phase 1 — fan-out specialist agents
        phase1_agents = [a for a in self.AGENTS if a["priority"] <= 2]
        if not run_governance:
            phase1_agents = [a for a in phase1_agents if a["role"] != "governance_analyst"]

        phase1_tasks = [
            self._run_chunked_agent(agent, chunks, protocol_name, complexity, analysis_id)
            for agent in phase1_agents
        ]
        phase1_results = await asyncio.gather(*phase1_tasks)

        risk_result = next((r for r in phase1_results if r["agent"] == "risk_scanner"), {})
        token_result = next((r for r in phase1_results if r["agent"] == "tokenomics_auditor"), {})
        gov_result = next((r for r in phase1_results if r["agent"] == "governance_analyst"), {})

        # Phase 2 — synthesis
        synth_context = (
            f"## Protocol\n{protocol_name}\n\n"
            f"## Complexity\n{complexity}\n\n"
            f"## Risk Scan\n{risk_result.get('result', 'N/A')}\n\n"
            f"## Tokenomics Audit\n{token_result.get('result', 'N/A')}\n\n"
            f"## Governance Analysis\n{gov_result.get('result', 'N/A')}\n\n"
        )
        thesis_result = await self.run_agent(
            "thesis_composer", snapshot, synth_context, analysis_id
        )

        total_tokens = (
            sum(r.get("tokens_used", 0) for r in phase1_results)
            + thesis_result.get("tokens_used", 0)
        )
        total_elapsed = round(time.time() - start_time, 2)

        self.tracker.record_analysis()

        return {
            "analysis_id": analysis_id,
            "protocol_name": protocol_name,
            "complexity": complexity,
            "pipeline": {
                "risk_scan": risk_result,
                "tokenomics_audit": token_result,
                "governance_analysis": gov_result,
                "thesis_synthesis": thesis_result,
            },
            "report": thesis_result.get("result", ""),
            "total_tokens_used": total_tokens,
            "total_elapsed_seconds": total_elapsed,
            "agents_used": len(phase1_agents) + 1,
            "chunks_processed": len(chunks),
        }
