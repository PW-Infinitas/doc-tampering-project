# VLM Fraud Detection — Architecture Rationale

## Goal
Systematically evaluate whether Gemini models via Vertex AI can detect tampering in Thai financial documents. The design prioritises **reproducibility** and **extensibility** — every run must be traceable back to exact inputs, and adding a new model or prompt should require zero structural change.

---

## Project Structure Decisions

### `config.py` — single source of truth
All constants live here so changing a model name, iteration count, or rate limit is a one-line edit and propagates everywhere. No magic strings scattered across files.

### `utils/schema.py` — dataclasses over dicts
Python dicts are error-prone when your result has 15+ fields. Dataclasses give:
- Type hints that IDEs and linters can check
- `asdict()` for free JSON serialisation
- A clear contract for what every result record contains

`ImageRecord` separates *what the image is* from *what the model said*. `EvalResult` captures both ground truth and prediction in one row — so analysis requires no joins.

### `utils/auth.py` — singleton client
Creating a Vertex AI client authenticates and opens a connection. Doing it once per script run (not once per API call) avoids repeated auth overhead across hundreds of calls. The global singleton pattern here is intentional — this is a script, not a web server.

### `utils/rate_limit.py` — decorator, not inline logic
Retry logic as a decorator keeps `evaluate.py` clean. The actual API call reads as a single line; the retry behaviour is a separate concern. Exponential backoff (`wait = base * attempt`) is standard practice — it gives the API time to recover without hammering it.

---

## Data Design Decisions

### `labels/manifest.csv` — ground truth decoupled from images
The manifest is the single record of what each image *is*. This means:
- You can re-run evals on the same images with new prompts without touching the data
- Analysis always has access to ground truth alongside predictions
- Adding new images means adding a CSV row, not changing any code

**Why CSV and not a database?** The dataset is small (tens to low hundreds of images). CSV is readable, version-controllable, and requires no setup.

### `tamper_types` and `augment_types` as JSON arrays in CSV
A single image can have multiple tamper types (e.g. text replacement + stamp overlay) and multiple augmentations. Storing them as JSON arrays (`["text_replacement","stamp_overlay"]`) avoids multi-row fan-out while keeping the manifest a flat file.

### `data/` subdirectory split
- `raw/` — originals, never modified
- `tampered/` — programmatically tampered variants (output of `data_prep/tamper.py`)
- `augmented/` — augmented variants (output of `data_prep/augment.py`)
- `standalone/` — isolated stamps and ตราครุฑ for targeted probing

Keeping originals untouched means you can always regenerate all variants from scratch.

---

## Data Prep Decisions

### `data_prep/tamper.py` — stubs, not implementations
Tampering requires deciding *how* to identify and replace regions (pure PIL draw vs OCR-guided vs OpenCV inpainting). That decision affects quality significantly and needs to be validated visually before committing to an approach. Stubs prevent premature implementation.

### `data_prep/augment.py` — brightness/noise/blur implemented, tilt as stub
Rotate, brightness, noise, and blur are straightforward PIL operations with no ambiguity. Tilt (perspective transform) requires OpenCV's `getPerspectiveTransform` and needs a separate dependency decision, so it's deferred.

Augmentation serves two purposes here:
1. Simulate real-world image variation (phone photos, scanners, lighting)
2. Test whether model performance degrades gracefully under degradation

---

## Prompt Library Decisions

### `prompts/library.py` — versioned, named prompts as a dict
Prompt wording is a test variable — just like model choice. Storing prompts with an `id` (e.g. `v1_zero_shot`) means every result row records exactly which prompt produced it. When you iterate on wording, bump the version (`v2_zero_shot`) rather than overwriting, so old results remain interpretable.

### Five prompt strategies chosen
| Prompt | Why |
|---|---|
| `v1_zero_shot` | Baseline. Minimal instruction, binary answer. |
| `v1_cot` | Chain-of-thought forces the model to reason element-by-element before concluding — reduces confident wrong answers. |
| `v1_structured` | JSON output is machine-parseable. Avoids writing regex to extract yes/no from prose. |
| `v1_targeted_stamp` | Stamps are the hardest forgery target. Isolating the question removes noise from the rest of the document. |
| `v1_targeted_text` | Text field replacement (salary, name, date) is the most common real-world tamper. Targeted probe gives cleaner signal. |

---

## Evaluation Loop Decisions (`evaluate.py`)

### Loop order: `images → models → prompts → iterations`
Iterating images in the outer loop means if the run is interrupted, you have complete results for all models/prompts on the images processed so far — not partial results for one model.

### `N_ITERATIONS = 3` per combination
Gemini models are non-deterministic at default temperature. Running each combination 3 times lets you measure consistency (does the model always agree with itself?) separately from accuracy. A model that answers correctly but inconsistently is less useful in production than one that is consistently slightly wrong.

### JSONL output (not CSV)
Each result is written as a single JSON line and flushed immediately. This means:
- If the run crashes at image 80 of 100, you have 80 complete rows — not a corrupted CSV
- Appending across multiple partial runs is safe
- Each row is self-contained with full context (no column alignment issues with nested lists)

### Rate limiting inside the loop
`min_gap = 60 / RATE_LIMIT_RPM` ensures average throughput stays under quota. The sleep only happens if the call completed faster than the gap — fast calls sleep, slow calls don't. This is more accurate than a fixed `time.sleep` after every call.

---

## What's Deliberately Left Out

- **No database** — dataset is too small to justify the overhead
- **No async/parallel calls** — rate limit is the bottleneck; parallelism would hit quota and complicate retry logic
- **No logging framework** — `print()` is sufficient for a script; logs go to terminal or can be redirected to a file
- **No CLI argument parser yet** — `run_evaluation(prompt_ids=..., model_names=...)` covers filtering needs for now; add `argparse` when running from cron or CI
