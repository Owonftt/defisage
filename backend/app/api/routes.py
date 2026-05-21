"""DeFiSage API routes — protocol intelligence, batch analysis, Q&A, stats."""

import asyncio
import time
from typing import Optional

from fastapi import APIRouter, File, Form, HTTPException, Request, UploadFile
from pydantic import BaseModel

from app.core.token_tracker import TokenTracker
from app.services.analysis_pipeline import ProtocolAnalysisPipeline
from app.services.mimo_client import MiMoClient
from app.utils.snapshot_validator import scaffold_snapshot, validate_snapshot

router = APIRouter()


class AnalyzeRequest(BaseModel):
    snapshot: str
    protocol_name: Optional[str] = None
    chain: Optional[str] = "Ethereum"
    run_governance: bool = True


class BatchAnalyzeRequest(BaseModel):
    protocols: list[AnalyzeRequest]
    parallel: bool = True
    max_concurrent: int = 3


class ChatRequest(BaseModel):
    message: str
    context: Optional[str] = None


class ScaffoldRequest(BaseModel):
    protocol_name: str
    chain: Optional[str] = "Ethereum"


def _get_pipeline(request: Request) -> ProtocolAnalysisPipeline:
    mimo: MiMoClient = request.app.state.mimo_client
    tracker: TokenTracker = request.app.state.token_tracker
    return ProtocolAnalysisPipeline(mimo, tracker)


@router.post("/analyze")
async def analyze_protocol(req: AnalyzeRequest, request: Request):
    """Run the multi-agent pipeline against a single protocol snapshot."""
    if not req.snapshot.strip():
        raise HTTPException(400, "Snapshot is empty")

    validation = validate_snapshot(req.snapshot)
    pipeline = _get_pipeline(request)
    name = req.protocol_name or "Unknown Protocol"

    result = await pipeline.analyze(req.snapshot, name, run_governance=req.run_governance)
    result["validation"] = validation
    result["chain_hint"] = req.chain
    return result


@router.post("/batch-analyze")
async def batch_analyze(req: BatchAnalyzeRequest, request: Request):
    """Run the pipeline against multiple protocols at once."""
    if len(req.protocols) > 10:
        raise HTTPException(400, "Maximum 10 protocols per batch")

    pipeline = _get_pipeline(request)

    if req.parallel:
        sem = asyncio.Semaphore(max(1, req.max_concurrent))

        async def limited(p: AnalyzeRequest) -> dict:
            async with sem:
                name = p.protocol_name or "Unknown Protocol"
                return await pipeline.analyze(p.snapshot, name, run_governance=p.run_governance)

        coros = [limited(p) for p in req.protocols]
        results = await asyncio.gather(*coros, return_exceptions=True)
        normalized = [
            r if not isinstance(r, Exception) else {"error": str(r)} for r in results
        ]
        return {
            "batch_id": str(int(time.time())),
            "total_protocols": len(req.protocols),
            "parallel": True,
            "results": normalized,
        }

    results = []
    for p in req.protocols:
        name = p.protocol_name or "Unknown Protocol"
        results.append(
            await pipeline.analyze(p.snapshot, name, run_governance=p.run_governance)
        )
    return {
        "batch_id": str(int(time.time())),
        "total_protocols": len(req.protocols),
        "parallel": False,
        "results": results,
    }


@router.post("/upload")
async def upload_snapshot(
    file: UploadFile = File(...),
    protocol_name: Optional[str] = Form(None),
    chain: Optional[str] = Form("Ethereum"),
    request: Request = None,
):
    """Upload a Markdown / text protocol snapshot for analysis."""
    allowed_ext = (".md", ".txt", ".markdown")
    if not file.filename or not file.filename.lower().endswith(allowed_ext):
        raise HTTPException(400, f"Only {allowed_ext} files are supported")

    content = (await file.read()).decode("utf-8", errors="ignore")
    name = protocol_name or file.filename.rsplit(".", 1)[0]
    pipeline = _get_pipeline(request)
    result = await pipeline.analyze(content, name)
    result["chain_hint"] = chain
    return result


@router.post("/scaffold")
async def scaffold(req: ScaffoldRequest):
    """Return a snapshot scaffold the user can fill in."""
    return {"snapshot": scaffold_snapshot(req.protocol_name, req.chain or "Ethereum")}


@router.post("/chat")
async def chat_with_agent(req: ChatRequest, request: Request):
    """Q&A with the DeFi research copilot."""
    mimo: MiMoClient = request.app.state.mimo_client
    tracker: TokenTracker = request.app.state.token_tracker

    system = (
        "You are DeFiSage AI, an institutional DeFi research analyst. Answer questions "
        "about protocol risk, tokenomics, governance, and market structure with rigor. "
        "Reference real protocols and historical incidents when relevant. Distinguish "
        "facts from speculation. Keep answers actionable for portfolio managers."
    )
    if req.context:
        system += f"\n\nUser-provided context:\n{req.context}"

    result = await mimo.chat(
        messages=[{"role": "user", "content": req.message}],
        system=system,
        temperature=0.4,
    )

    tokens = result.get("tokens", {}).get("total", 0)
    tracker.record_usage(tokens, agent="chat_agent")

    return {
        "response": result.get("content", ""),
        "tokens_used": tokens,
        "model": result.get("model"),
        "elapsed_seconds": result.get("elapsed_seconds"),
    }


@router.get("/stats")
async def get_stats(request: Request):
    """Get token usage statistics."""
    tracker: TokenTracker = request.app.state.token_tracker
    return tracker.get_stats()


@router.get("/stats/history")
async def get_stats_history(request: Request, limit: int = 50):
    """Get recent token usage history."""
    tracker: TokenTracker = request.app.state.token_tracker
    return {"history": tracker.get_history(limit)}


@router.get("/stats/trend")
async def get_stats_trend(request: Request, days: int = 7):
    """Get daily token usage trend."""
    tracker: TokenTracker = request.app.state.token_tracker
    return {"trend": tracker.get_daily_trend(days)}


@router.get("/agents")
async def list_agents():
    """Expose the agent roles + their roles for UI rendering."""
    from app.services.mimo_client import AGENT_PROMPTS

    return {
        "agents": [
            {"role": role, "system_prompt_preview": prompt[:240] + "..."}
            for role, prompt in AGENT_PROMPTS.items()
        ]
    }
