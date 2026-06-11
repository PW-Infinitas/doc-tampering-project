"""Append-only logger for prompt_optimisation.ipynb experiment results."""

import json
from datetime import datetime, timezone
from pathlib import Path

import pandas as pd

RESULTS_DIR = Path(__file__).parent / "notebook_results"
LOG_PATH = RESULTS_DIR / "results_log.jsonl"


def log_result(
    batch_id: str,
    image_path: str,
    prompt_id: str,
    model: str,
    raw_response: str,
    temperature: float | None = None,
    latency_s: float | None = None,
    notes: str = "",
) -> None:
    """Append one experiment result as a JSON line to notebook_results/results_log.jsonl."""
    record = {
        "timestamp": datetime.now(timezone.utc).isoformat(),
        "batch_id": batch_id,
        "image_path": str(image_path),
        "prompt_id": prompt_id,
        "model": model,
        "temperature": temperature,
        "latency_s": latency_s,
        "raw_response": raw_response,
        "parsed_response": _try_parse_json(raw_response),
        "notes": notes,
    }

    RESULTS_DIR.mkdir(exist_ok=True)
    with open(LOG_PATH, "a", encoding="utf-8") as f:
        f.write(json.dumps(record, ensure_ascii=False) + "\n")


def _try_parse_json(raw_response: str) -> dict | None:
    cleaned = raw_response.strip()
    if cleaned.startswith("```"):
        cleaned = cleaned.removeprefix("```json").removeprefix("```").removesuffix("```").strip()
    try:
        return json.loads(cleaned)
    except json.JSONDecodeError:
        return None


def load_results(batch_id: str | None = None) -> pd.DataFrame:
    """Load all logged results as a DataFrame, optionally filtered to one batch_id."""
    if not LOG_PATH.exists():
        return pd.DataFrame()

    rows = [
        json.loads(line)
        for line in LOG_PATH.read_text(encoding="utf-8").splitlines()
        if line.strip()
    ]
    df = pd.DataFrame(rows)

    if batch_id is not None:
        df = df[df["batch_id"] == batch_id]

    return df
