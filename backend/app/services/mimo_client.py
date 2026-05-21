"""MiMo API client — OpenAI-compatible interface tailored for DeFi protocol analysis agents."""

import time
from typing import AsyncGenerator, Optional

from openai import AsyncOpenAI


AGENT_PROMPTS = {
    "risk_scanner": (
        "You are a senior DeFi risk analyst. Given a structured snapshot of a live DeFi "
        "protocol (TVL history, oracle dependencies, audit history, key contracts, exploit "
        "register), produce a deep risk assessment. Cover: smart contract risk surface, "
        "oracle/feed risk, custody / multisig posture, bridge or cross-chain dependencies, "
        "centralization risks, historical incident patterns, and mitigations actually live "
        "today. Output structured findings with severity ratings (Critical / High / Medium / "
        "Low / Informational) and a final 0-100 risk score with justification."
    ),
    "tokenomics_auditor": (
        "You are a tokenomics auditor. Given on-chain token data (supply, holders, vesting, "
        "emissions, fees, treasury) for a DeFi protocol, evaluate: emission pressure vs "
        "demand sinks, holder concentration (Gini, top-10 share), vesting cliffs and unlock "
        "calendar, fee/rev capture mechanism, treasury runway, and incentive sustainability. "
        "Output a structured tokenomics health report with quantitative metrics, "
        "scenario-based unlock impact projections, and a 0-100 tokenomics score."
    ),
    "governance_analyst": (
        "You are a DAO governance analyst. Given proposal history, voter participation, "
        "delegate distribution, timelock parameters, multisig signers, and contract upgrade "
        "patterns, evaluate: voter concentration, plutocracy risk, capture vectors, "
        "emergency/upgrade powers, timelock effectiveness, dispute resolution, and "
        "transparency. Output a governance health report with concrete attack scenarios "
        "the protocol is exposed to, and a 0-100 governance score."
    ),
    "thesis_composer": (
        "You are an institutional research analyst writing the final synthesis report for "
        "an investment desk. Given the outputs from the Risk, Tokenomics, and Governance "
        "agents, compose a polished IR-grade memo that includes: executive summary, "
        "investment thesis (bull / bear / base case), composite risk rating, capital "
        "allocation guidance with sizing bands, monitoring KPIs to watch weekly, and "
        "explicit kill-switches that would invalidate the thesis. Use clean markdown with "
        "headings, tables, and severity icons. Keep it actionable for portfolio managers."
    ),
    "qa_assistant": (
        "You are DeFiSage's interactive DeFi research copilot. Answer the user's question "
        "with rigor: cite specific protocols, on-chain mechanisms, and historical "
        "incidents. Distinguish facts from speculation. When numbers are uncertain, say "
        "so. Always conclude with two or three monitoring questions the user should keep "
        "asking themselves."
    ),
}


class MiMoClient:
    """Async client for Xiaomi MiMo API (OpenAI-compatible)."""

    def __init__(self, api_key: str, base_url: str, model: str):
        self.model = model
        self.client = AsyncOpenAI(
            api_key=api_key or "demo-key",
            base_url=base_url,
            timeout=120.0,
            max_retries=3,
        )

    async def chat(
        self,
        messages: list[dict],
        temperature: float = 0.25,
        max_tokens: int = 4096,
        system: Optional[str] = None,
    ) -> dict:
        """Single chat completion with token tracking."""
        if system:
            messages = [{"role": "system", "content": system}] + messages

        start = time.time()
        try:
            response = await self.client.chat.completions.create(
                model=self.model,
                messages=messages,
                temperature=temperature,
                max_tokens=max_tokens,
            )
            elapsed = time.time() - start
            usage = response.usage
            return {
                "content": response.choices[0].message.content,
                "tokens": {
                    "prompt": usage.prompt_tokens if usage else 0,
                    "completion": usage.completion_tokens if usage else 0,
                    "total": usage.total_tokens if usage else 0,
                },
                "elapsed_seconds": round(elapsed, 2),
                "model": self.model,
            }
        except Exception as e:
            return {
                "content": None,
                "error": str(e),
                "tokens": {"prompt": 0, "completion": 0, "total": 0},
                "elapsed_seconds": round(time.time() - start, 2),
                "model": self.model,
            }

    async def analyze_protocol(
        self,
        snapshot: str,
        agent_role: str,
        context: str = "",
        temperature: float = 0.25,
        max_tokens: int = 4096,
    ) -> dict:
        """Analyze a protocol snapshot with a specific agent role."""
        system_prompt = AGENT_PROMPTS.get(agent_role, AGENT_PROMPTS["risk_scanner"])
        if context:
            system_prompt += f"\n\nAdditional context:\n{context}"

        return await self.chat(
            messages=[{"role": "user", "content": f"```protocol-snapshot\n{snapshot}\n```"}],
            system=system_prompt,
            temperature=temperature,
            max_tokens=max_tokens,
        )

    async def stream_chat(
        self,
        messages: list[dict],
        system: Optional[str] = None,
    ) -> AsyncGenerator[str, None]:
        """Stream chat completion."""
        if system:
            messages = [{"role": "system", "content": system}] + messages

        stream = await self.client.chat.completions.create(
            model=self.model,
            messages=messages,
            stream=True,
            temperature=0.3,
        )

        async for chunk in stream:
            if chunk.choices[0].delta.content:
                yield chunk.choices[0].delta.content
