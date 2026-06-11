"""Append-only logger for prompt_optimisation.ipynb experiment results."""

import json
from datetime import datetime, timezone
from pathlib import Path

import pandas as pd

RESULTS_DIR = Path(__file__).parent / "notebook_results"
LOG_PATH = RESULTS_DIR / "results_log.jsonl"

EXPECTED_VERDICTS = {"tampered", "authentic", "inconclusive"}
EXPECTED_CONFIDENCE_LEVELS = {"high", "medium", "low"}
EXPECTED_SEVERITY_LEVELS = {"high", "medium", "low"}
EXPECTED_SIGNAL_TYPES = {
    "font_weight_inconsistency",
    "resolution_mismatch",
    "baseline_mismatch",
    "shadow_edge_anomaly",
    "color_contrast_discontinuity",
    "font_size_mismatch",
    "background_overlay",
    "other",
}


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


def _extract_signal_types(parsed: dict | None) -> list[str]:
    if not isinstance(parsed, dict):
        return []

    signals = parsed.get("signals_detected")
    if not isinstance(signals, list):
        return []

    return [
        signal["signal_type"]
        for signal in signals
        if isinstance(signal, dict) and "signal_type" in signal
    ]


def _matches_expected_schema(parsed: dict | None) -> bool:
    """Check whether a parsed response matches the V2 prompt's output schema."""
    if not isinstance(parsed, dict):
        return False

    if parsed.get("verdict") not in EXPECTED_VERDICTS:
        return False

    if parsed.get("confidence") not in EXPECTED_CONFIDENCE_LEVELS:
        return False

    if not isinstance(parsed.get("reasoning"), str):
        return False

    signals = parsed.get("signals_detected")
    if not isinstance(signals, list):
        return False

    for signal in signals:
        if not isinstance(signal, dict):
            return False
        if signal.get("signal_type") not in EXPECTED_SIGNAL_TYPES:
            return False
        if not isinstance(signal.get("location"), str):
            return False
        if signal.get("severity") not in EXPECTED_SEVERITY_LEVELS:
            return False

    return "notes" in parsed


def load_results(batch_id: str | None = None) -> pd.DataFrame:
    """Load all logged results as a DataFrame, optionally filtered to one batch_id.

    Adds derived columns parsed from `parsed_response`:
    - verdict, confidence: pulled directly from the response
    - signal_types: list of signal_type values from signals_detected (empty if none)
    - format: True if the response matches the expected V2 schema, else False
    """
    if not LOG_PATH.exists():
        return pd.DataFrame()

    rows = [
        json.loads(line)
        for line in LOG_PATH.read_text(encoding="utf-8").splitlines()
        if line.strip()
    ]
    if not rows:
        return pd.DataFrame()

    df = pd.DataFrame(rows)

    if batch_id is not None:
        df = df[df["batch_id"] == batch_id]

    df["verdict"] = df["parsed_response"].apply(
        lambda parsed: parsed.get("verdict") if isinstance(parsed, dict) else None
    )
    df["confidence"] = df["parsed_response"].apply(
        lambda parsed: parsed.get("confidence") if isinstance(parsed, dict) else None
    )
    df["signal_types"] = df["parsed_response"].apply(_extract_signal_types)
    df["format"] = df["parsed_response"].apply(_matches_expected_schema)

    return df
