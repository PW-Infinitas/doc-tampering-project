import csv
import json
import time
from dataclasses import asdict
from pathlib import Path

import mlflow
from PIL import Image

from config import (
    MODELS, N_ITERATIONS, LABELS_PATH, RESULTS_DIR, RATE_LIMIT_RPM,
    MLFLOW_EXPERIMENT, MLFLOW_TRACKING_URI,
)
from prompts.library import PROMPT_LIBRARY
from utils.auth import get_client
from utils.rate_limit import with_retry
from utils.schema import EvalResult, ImageRecord


def load_manifest(manifest_path: Path, split: str | None = None) -> list[ImageRecord]:
    records = []
    with open(manifest_path, newline="", encoding="utf-8") as f:
        for row in csv.DictReader(f):
            if split and row.get("split", "dev") != split:
                continue
            records.append(ImageRecord(
                image_id=row["image_id"],
                image_path=row["image_path"],
                doc_type=row["doc_type"],  # type: ignore[arg-type]
                is_tampered=row["is_tampered"].lower() == "true",
                tamper_types=json.loads(row["tamper_types"]),
                severity=row["severity"],  # type: ignore[arg-type]
                is_augmented=row["is_augmented"].lower() == "true",
                augment_types=json.loads(row["augment_types"]),
                image_quality=row["image_quality"],  # type: ignore[arg-type]
                source_image_id=row.get("source_image_id") or None,
                split=row.get("split", "dev"),  # type: ignore[arg-type]
            ))
    return records


@with_retry
def call_model(client, model: str, prompt: str, image: Image.Image) -> tuple[str, float]:
    start = time.perf_counter()
    response = client.models.generate_content(
        model=model,
        contents=[prompt, image],
    )
    return response.text, round(time.perf_counter() - start, 2)


def parse_response(raw: str, prompt_strategy: str) -> tuple[bool | None, list[str], str]:
    """Return (predicted_tampered, predicted_tamper_types, rationale)."""
    if prompt_strategy == "structured_output":
        try:
            cleaned = raw.strip().removeprefix("```json").removesuffix("```").strip()
            data = json.loads(cleaned)
            return data.get("tampered"), [], data.get("rationale", "")
        except json.JSONDecodeError:
            return None, [], raw
    if prompt_strategy == "zero_shot":
        lowered = raw.strip().lower()
        if lowered.startswith("yes"):
            return True, [], ""
        if lowered.startswith("no"):
            return False, [], ""
        return None, [], raw
    return None, [], raw


def run_evaluation(
    prompt_ids: list[str] | None = None,
    model_names: list[str] | None = None,
    split: str | None = "dev",
) -> Path:
    mlflow.set_tracking_uri(MLFLOW_TRACKING_URI)
    mlflow.set_experiment(MLFLOW_EXPERIMENT)

    client = get_client()
    records = load_manifest(LABELS_PATH, split=split)
    prompts = {k: v for k, v in PROMPT_LIBRARY.items() if prompt_ids is None or k in prompt_ids}
    models = model_names or MODELS

    min_gap = 60 / RATE_LIMIT_RPM
    timestamp = int(time.time())
    RESULTS_DIR.mkdir(exist_ok=True)
    output_path = RESULTS_DIR / f"eval_{timestamp}.jsonl"

    run_name = f"eval_{timestamp}_{'_'.join(models)}"

    with mlflow.start_run(run_name=run_name):
        mlflow.log_params({
            "models": ",".join(models),
            "prompt_ids": ",".join(prompts.keys()),
            "n_iterations": N_ITERATIONS,
            "n_images": len(records),
            "split": split or "all",
        })

        total_calls = 0
        error_count = 0
        total_latency = 0.0

        with open(output_path, "w", encoding="utf-8") as out:
            for record in records:
                image = Image.open(record.image_path)
                for model in models:
                    for prompt_id, prompt in prompts.items():
                        for iteration in range(1, N_ITERATIONS + 1):
                            result = EvalResult(
                                image_id=record.image_id,
                                doc_type=record.doc_type,
                                is_tampered=record.is_tampered,
                                tamper_types=record.tamper_types,
                                severity=record.severity,
                                image_quality=record.image_quality,
                                model=model,
                                prompt_id=prompt_id,
                                iteration=iteration,
                                predicted_tampered=None,
                            )
                            try:
                                t0 = time.time()
                                raw, latency = call_model(client, model, prompt["text"], image)
                                predicted, pred_types, rationale = parse_response(raw, prompt["strategy"])
                                result.raw_response = raw
                                result.predicted_tampered = predicted
                                result.predicted_tamper_types = pred_types
                                result.rationale = rationale
                                result.latency_s = latency
                                total_latency += latency
                                elapsed = time.time() - t0
                                if elapsed < min_gap:
                                    time.sleep(min_gap - elapsed)
                            except Exception as e:
                                result.error = str(e)
                                error_count += 1

                            total_calls += 1
                            out.write(json.dumps(asdict(result), ensure_ascii=False) + "\n")
                            out.flush()

        successful = total_calls - error_count
        mlflow.log_metrics({
            "total_calls": total_calls,
            "error_count": error_count,
            "avg_latency_s": round(total_latency / max(1, successful), 2),
        })
        mlflow.log_artifact(str(output_path))
        mlflow.set_tag("results_file", output_path.name)

    print(f"Done. Results: {output_path}")
    return output_path


if __name__ == "__main__":
    run_evaluation()
