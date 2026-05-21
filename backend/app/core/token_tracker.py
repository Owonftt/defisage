"""Token usage tracking for MiMo API calls in the DeFiSage pipeline."""

import json
import os
import time
from collections import defaultdict
from datetime import date, datetime, timedelta
from threading import Lock

from app.core.config import settings


class TokenTracker:
    """Tracks daily API token consumption across all analysis pipelines."""

    LOG_FILE = os.path.expanduser("~/projects/defisage/backend/token_usage.jsonl")

    def __init__(self):
        self._lock = Lock()
        self._start_time = time.time()
        self._daily_tokens = defaultdict(int)
        self._daily_calls = defaultdict(int)
        self._analyses = defaultdict(int)
        self._agent_tokens = defaultdict(lambda: defaultdict(int))
        self._history = []

    def _today(self) -> str:
        return date.today().isoformat()

    def record_usage(self, tokens: int, agent: str = "general", analysis_id: str = ""):
        """Record token usage from an API call."""
        with self._lock:
            today = self._today()
            self._daily_tokens[today] += tokens
            self._daily_calls[today] += 1
            self._agent_tokens[today][agent] += tokens

            entry = {
                "timestamp": datetime.now().isoformat(),
                "tokens": tokens,
                "agent": agent,
                "analysis_id": analysis_id,
                "daily_total": self._daily_tokens[today],
            }
            self._history.append(entry)

            try:
                os.makedirs(os.path.dirname(self.LOG_FILE), exist_ok=True)
                with open(self.LOG_FILE, "a") as f:
                    f.write(json.dumps(entry) + "\n")
            except Exception:
                pass

    def record_analysis(self):
        """Record a completed analysis."""
        with self._lock:
            self._analyses[self._today()] += 1

    def get_stats(self) -> dict:
        """Get current token usage statistics."""
        today = self._today()
        with self._lock:
            budget = max(settings.DAILY_TOKEN_BUDGET, 1)
            return {
                "date": today,
                "total_tokens_today": self._daily_tokens[today],
                "api_calls_today": self._daily_calls[today],
                "analyses_completed": self._analyses[today],
                "agent_breakdown": dict(self._agent_tokens[today]),
                "uptime_seconds": int(time.time() - self._start_time),
                "budget_total": budget,
                "budget_used_pct": round(self._daily_tokens[today] / budget * 100, 2),
            }

    def get_history(self, limit: int = 100) -> list:
        """Get recent token usage history."""
        with self._lock:
            return self._history[-limit:]

    def get_daily_trend(self, days: int = 7) -> list:
        """Get token usage trend for the last N days."""
        today = date.today()
        trend = []
        with self._lock:
            for i in range(days):
                d = (today - timedelta(days=i)).isoformat()
                trend.append({
                    "date": d,
                    "tokens": self._daily_tokens.get(d, 0),
                    "calls": self._daily_calls.get(d, 0),
                    "analyses": self._analyses.get(d, 0),
                })
        return list(reversed(trend))
