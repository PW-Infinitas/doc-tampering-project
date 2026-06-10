import json
import sys
from pathlib import Path

import mlflow
import pandas as pd
from sklearn.metrics import precision_score, recall_score, f1_score, confusion_matrix

from config import MLFLOW_EXPERIMENT, MLFLOW_TRACKING_URI


def load_results(jsonl_path: Path) -> pd.DataFrame:
    rows = [json.loads(line) for line in jsonl_path.read_text(encoding="utf-8").splitlines() if line.strip()]
    return pd.DataFrame(rows)


def majority_vote(df: pd.DataFrame) -> pd.DataFrame:
    """Collapse N iterations per (image_id, model, prompt_id) into one row via majority vote.

    Also computes consistency_rate: fraction of groups where all iterations agreed.
    """
    parseable = df[df["predicted_tampered"].notna()].copy()
    parseable["predicted_tampered"] = parseable["predicted_tampered"].astype(bool)

    groups = parseable.groupby(["image_id", "model", "prompt_id"])

    voted_rows = []
    for (image_id, model, prompt_id), grp in groups:
        votes = grp["predicted_tampered"]
        majority = votes.sum() > len(votes) / 2
        unanimous = votes.nunique() == 1
        voted_rows.append({
            "image_id": image_id,
            "model": model,
            "prompt_id": prompt_id,
            "is_tampered": grp["is_tampered"].iloc[0],
            "doc_type": grp["doc_type"].iloc[0],
            "severity": grp["severity"].iloc[0],
            "image_quality": grp["image_quality"].iloc[0],
            "tamper_types": grp["tamper_types"].iloc[0],
            "predicted_tampered": majority,
            "unanimous": unanimous,
            "n_iterations": len(grp),
        })

    return pd.DataFrame(voted_rows)


def compute_metrics(voted: pd.DataFrame) -> pd.DataFrame:
    """Return a summary DataFrame with one row per (model, prompt_id)."""
    summary_rows = []

    for (model, prompt_id), grp in voted.groupby(["model", "prompt_id"]):
        y_true = grp["is_tampered"].astype(bool)
        y_pred = grp["predicted_tampered"].astype(bool)

        tn, fp, fn, tp = confusion_matrix(y_true, y_pred, labels=[False, True]).ravel()

        summary_rows.append({
            "model": model,
            "prompt_id": prompt_id,
            "n_images": len(grp),
            "precision": round(precision_score(y_true, y_pred, zero_division=0), 3),
            "recall": round(recall_score(y_true, y_pred, zero_division=0), 3),
            "f1": round(f1_score(y_true, y_pred, zero_division=0), 3),
            "consistency_rate": round(grp["unanimous"].mean(), 3),
            "tp": int(tp),
            "fp": int(fp),
            "tn": int(tn),
            "fn": int(fn),
        })

    return pd.DataFrame(summary_rows).sort_values("recall", ascending=False)


def slice_metrics(voted: pd.DataFrame, by: str) -> pd.DataFrame:
    """Compute recall/precision/F1 broken down by an additional dimension (severity, doc_type, etc.)."""
    # TODO: implement per-slice metrics for deeper failure analysis
    raise NotImplementedError(f"Slice analysis by '{by}' not yet implemented")


def log_to_mlflow(summary: pd.DataFrame, jsonl_path: Path) -> None:
    mlflow.set_tracking_uri(MLFLOW_TRACKING_URI)
    mlflow.set_experiment(MLFLOW_EXPERIMENT)

    for _, row in summary.iterrows():
        run_name = f"score_{row['model']}_{row['prompt_id']}"
        with mlflow.start_run(run_name=run_name):
            mlflow.set_tag("run_type", "scoring")
            mlflow.set_tag("source_file", jsonl_path.name)
            mlflow.log_params({
                "model": row["model"],
                "prompt_id": row["prompt_id"],
                "n_images": row["n_images"],
            })
            mlflow.log_metrics({
                "precision": row["precision"],
                "recall": row["recall"],
                "f1": row["f1"],
                "consistency_rate": row["consistency_rate"],
                "tp": row["tp"],
                "fp": row["fp"],
                "tn": row["tn"],
                "fn": row["fn"],
            })


def score(jsonl_path: Path, log_mlflow: bool = True) -> pd.DataFrame:
    df = load_results(jsonl_path)
    voted = majority_vote(df)
    summary = compute_metrics(voted)

    print("\n── Scores by model × prompt ─────────────────────────────")
    print(summary.to_string(index=False))
    print()

    if log_mlflow:
        log_to_mlflow(summary, jsonl_path)
        print(f"Logged to MLflow experiment '{MLFLOW_EXPERIMENT}'")
        print(f"Run: mlflow ui --backend-store-uri {MLFLOW_TRACKING_URI}")

    return summary


if __name__ == "__main__":
    if len(sys.argv) < 2:
        print("Usage: python score.py <path/to/eval_*.jsonl>")
        sys.exit(1)
    score(Path(sys.argv[1]))
