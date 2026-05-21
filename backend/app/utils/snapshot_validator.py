"""Lightweight protocol-snapshot validator + scaffold for downstream agents."""

from __future__ import annotations

import re

ETH_ADDR_RE = re.compile(r"^0x[a-fA-F0-9]{40}$")


REQUIRED_SECTIONS = (
    "OVERVIEW",
    "TVL",
    "CONTRACTS",
    "TOKENOMICS",
    "GOVERNANCE",
    "INCIDENTS",
)


def validate_snapshot(snapshot: str) -> dict:
    """Run cheap structural checks on a protocol snapshot before we fan out to agents.

    Snapshot format expected:
        # OVERVIEW
        ...
        # TVL
        ...
        # CONTRACTS
        - Address: 0x...
        - Chain: Ethereum
        ...
    """
    issues: list[str] = []
    snapshot = snapshot or ""
    upper = snapshot.upper()

    if len(snapshot) < 200:
        issues.append("snapshot is too short (<200 chars); enrich before analysis")

    missing = [s for s in REQUIRED_SECTIONS if s not in upper]
    if missing:
        issues.append(f"missing recommended sections: {', '.join(missing)}")

    addresses = sorted(set(ETH_ADDR_RE.findall(line) for line in snapshot.split("\n") if ETH_ADDR_RE.match(line.strip())))
    addresses = [a for a in re.findall(r"0x[a-fA-F0-9]{40}", snapshot) if a.lower() != "0x" + "0" * 40]
    deduped = sorted(set(addresses))

    if not deduped:
        issues.append("no contract addresses detected — agents will run blind")

    return {
        "ok": not issues,
        "issues": issues,
        "addresses": deduped[:25],
        "size_bytes": len(snapshot),
        "lines": snapshot.count("\n") + 1,
    }


def scaffold_snapshot(protocol_name: str, chain: str = "Ethereum") -> str:
    """Return a minimal valid snapshot scaffold the user can fill in."""
    return (
        f"# OVERVIEW\nName: {protocol_name}\nChain: {chain}\nCategory: \nLaunch date: \n\n"
        "# TVL\nCurrent: $\n7d change: %\n30d change: %\nPeak TVL: $\n\n"
        "# CONTRACTS\n- Core router: 0x...\n- Treasury: 0x...\n- Token: 0x...\n\n"
        "# TOKENOMICS\nTotal supply: \nCirculating: \nUnlocks (next 90d): \nEmissions/day: \n"
        "Top-10 holders share: %\nFee accrual: \n\n"
        "# GOVERNANCE\nVoting venue: snapshot.org / tally.xyz\nQuorum: \nTimelock: \n"
        "Multisig signers: \nUpgrade pattern: \n\n"
        "# INCIDENTS\n(post-mortem links, exploit history, blocked attacks)\n"
    )
