"""
Zero-Authentication Auto-Discovery & Auto-Configuration Engine for C-DAC PARAM Shavak & Campus LAN Qwen Deployments.

How it works without authentication or manual model/port details:
1. Multi-Port Protocol Probing:
   Automatically scans standard unauthenticated inference ports on the target host/IP:
   - Port 11434 (/api/tags) -> Native Ollama Server (Zero-Auth)
   - Port 8000 (/v1/models) -> vLLM / HuggingFace TGI OpenAI-Compatible Server (Zero-Auth)
   - Port 8080 (/v1/models) -> llama.cpp / LocalAI OpenAI-Compatible Server (Zero-Auth)
   - Port 11434 (/v1/models) -> Ollama OpenAI-Compatible Endpoint (Zero-Auth)

2. Dynamic Model Tag Extraction:
   Queries the server's live model registry JSON (`/api/tags` or `/v1/models`), filters out embedding-only models,
   prioritizes deployed Qwen models (`qwen2.5`, `qwen2`, `qwen`, `deepseek`), and automatically binds the exact
   model identifier, protocol (`ollama` vs `vllm`), and base URL without requiring any API key or manual input.
"""

import os
import logging
from typing import Dict, Any, List, Optional
import httpx

logger = logging.getLogger(__name__)

CANDIDATE_ENDPOINTS = [
    {"port": 11434, "protocol": "ollama", "probe_path": "/api/tags", "base_suffix": ""},
    {"port": 8000, "protocol": "vllm", "probe_path": "/v1/models", "base_suffix": "/v1"},
    {"port": 8080, "protocol": "vllm", "probe_path": "/v1/models", "base_suffix": "/v1"},
    {"port": 1234, "protocol": "vllm", "probe_path": "/v1/models", "base_suffix": "/v1"},
]

EMBEDDING_KEYWORDS = ("embed", "nomic", "bge", "minilm", "e5-")


def _normalize_host(raw_host: str) -> str:
    """Strip http://, https://, ports, and trailing paths from a user-provided host or URL."""
    host = (raw_host or "").strip()
    if not host:
        host = os.getenv("PARAM_SHAVAK_HOST", os.getenv("OLLAMA_HOST", "localhost"))
    for prefix in ("http://", "https://"):
        if host.startswith(prefix):
            host = host[len(prefix):]
    host = host.split("/")[0]
    host = host.split(":")[0]
    return host or "localhost"


def _select_best_model(models: List[str], preferred_hint: str = "qwen") -> str:
    """
    Automatically selects the best deployed LLM from the server's model list:
    1. Exact match if preferred_hint is in models
    2. Any model containing 'qwen' (case-insensitive)
    3. Any model containing 'deepseek' or 'llama' or 'mistral'
    4. First non-embedding model
    """
    non_embed = [
        m for m in models
        if not any(ek in m.lower() for ek in EMBEDDING_KEYWORDS)
    ]
    pool = non_embed if non_embed else models
    if not pool:
        return "qwen2.5:14b"

    if preferred_hint and preferred_hint in pool:
        return preferred_hint

    for m in pool:
        if "qwen" in m.lower():
            return m

    for m in pool:
        if any(k in m.lower() for k in ("deepseek", "llama", "mistral", "gemma")):
            return m

    return pool[0]


def auto_discover_param_shavak_sync(
    raw_host: str = "localhost",
    timeout: float = 2.5,
    preferred_model: str = "qwen",
) -> Dict[str, Any]:
    """
    Synchronous zero-auth auto-discovery for Streamlit UI and CLI diagnostics.
    Probes candidate ports on `raw_host` without requiring any API key or authentication header.
    """
    host = _normalize_host(raw_host)
    attempted: List[str] = []

    for cand in CANDIDATE_ENDPOINTS:
        port = cand["port"]
        protocol = cand["protocol"]
        probe_url = f"http://{host}:{port}{cand['probe_path']}"
        base_url = f"http://{host}:{port}{cand['base_suffix']}"
        attempted.append(probe_url)

        try:
            # Zero-auth request (no API key needed; vLLM/Ollama accept unauthenticated GET on LAN)
            resp = httpx.get(probe_url, timeout=timeout)
            if resp.status_code == 200:
                payload = resp.json()
                discovered_models: List[str] = []

                if protocol == "ollama":
                    # Ollama /api/tags format: {"models": [{"name": "qwen2.5:14b", ...}]}
                    for item in payload.get("models", []):
                        name = item.get("name") or item.get("model")
                        if name:
                            discovered_models.append(name)
                else:
                    # OpenAI-compatible /v1/models format: {"data": [{"id": "Qwen/Qwen2.5-14B-Instruct", ...}]}
                    for item in payload.get("data", []):
                        model_id = item.get("id")
                        if model_id:
                            discovered_models.append(model_id)

                selected_model = _select_best_model(discovered_models, preferred_model)
                return {
                    "connected": True,
                    "host": host,
                    "port": port,
                    "protocol": protocol,
                    "base_url": base_url,
                    "probe_url": probe_url,
                    "discovered_models": discovered_models,
                    "selected_model": selected_model,
                    "auth_mode": "Zero-Auth (Unauthenticated Campus LAN / Local Socket)",
                    "attempted": attempted,
                }
        except Exception as exc:
            logger.debug(f"Auto-discovery probe failed for {probe_url}: {exc}")

    # Default fallback configuration if server is currently unreachable from this network
    return {
        "connected": False,
        "host": host,
        "port": 11434,
        "protocol": "ollama",
        "base_url": f"http://{host}:11434",
        "probe_url": f"http://{host}:11434/api/tags",
        "discovered_models": [],
        "selected_model": preferred_model if preferred_model != "qwen" else "qwen2.5:14b",
        "auth_mode": "Zero-Auth (Auto-Fallback Ready)",
        "attempted": attempted,
    }


async def auto_discover_param_shavak_async(
    raw_host_or_url: str = "localhost",
    timeout: float = 3.0,
    preferred_model: str = "qwen",
) -> Dict[str, Any]:
    """
    Asynchronous zero-auth auto-discovery used automatically inside CurriculumGenerator
    and AssessmentPlanGenerator before dispatching LLM inference calls.
    """
    host = _normalize_host(raw_host_or_url)
    attempted: List[str] = []

    async with httpx.AsyncClient(timeout=timeout) as client:
        for cand in CANDIDATE_ENDPOINTS:
            port = cand["port"]
            protocol = cand["protocol"]
            probe_url = f"http://{host}:{port}{cand['probe_path']}"
            base_url = f"http://{host}:{port}{cand['base_suffix']}"
            attempted.append(probe_url)

            try:
                resp = await client.get(probe_url)
                if resp.status_code == 200:
                    payload = resp.json()
                    discovered_models: List[str] = []
                    if protocol == "ollama":
                        for item in payload.get("models", []):
                            name = item.get("name") or item.get("model")
                            if name:
                                discovered_models.append(name)
                    else:
                        for item in payload.get("data", []):
                            model_id = item.get("id")
                            if model_id:
                                discovered_models.append(model_id)

                    selected_model = _select_best_model(discovered_models, preferred_model)
                    return {
                        "connected": True,
                        "host": host,
                        "port": port,
                        "protocol": protocol,
                        "base_url": base_url,
                        "probe_url": probe_url,
                        "discovered_models": discovered_models,
                        "selected_model": selected_model,
                        "auth_mode": "Zero-Auth (Unauthenticated Campus LAN / Local Socket)",
                        "attempted": attempted,
                    }
            except Exception:
                continue

    return {
        "connected": False,
        "host": host,
        "port": 11434,
        "protocol": "ollama",
        "base_url": f"http://{host}:11434",
        "probe_url": f"http://{host}:11434/api/tags",
        "discovered_models": [],
        "selected_model": preferred_model if preferred_model != "qwen" else "qwen2.5:14b",
        "auth_mode": "Zero-Auth (Auto-Fallback Ready)",
        "attempted": attempted,
    }
