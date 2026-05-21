"""DeFiSage configuration loaded from environment variables."""

import os
from dataclasses import dataclass


@dataclass
class Settings:
    # MiMo API
    MIMO_API_KEY: str = os.getenv("MIMO_API_KEY", "")
    MIMO_BASE_URL: str = os.getenv("MIMO_BASE_URL", "https://api.xiaomimimo.com/v1")
    MIMO_MODEL: str = os.getenv("MIMO_MODEL", "mimo-v2.5-pro")

    # Token budget
    DAILY_TOKEN_BUDGET: int = int(os.getenv("DAILY_TOKEN_BUDGET", "10000000"))

    # External data sources
    DEFILLAMA_BASE: str = os.getenv("DEFILLAMA_BASE", "https://api.llama.fi")
    COINGECKO_BASE: str = os.getenv("COINGECKO_BASE", "https://api.coingecko.com/api/v3")

    # Pipeline tuning
    AGENT_TEMPERATURE: float = float(os.getenv("AGENT_TEMPERATURE", "0.25"))
    AGENT_MAX_TOKENS: int = int(os.getenv("AGENT_MAX_TOKENS", "4096"))
    PROTOCOL_CHUNK_SIZE: int = int(os.getenv("PROTOCOL_CHUNK_SIZE", "180"))
    PROTOCOL_CHUNK_OVERLAP: int = int(os.getenv("PROTOCOL_CHUNK_OVERLAP", "20"))


settings = Settings()
