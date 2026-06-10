# VLM Fraud Detection — Project Log

## What This Project Is
Evaluate whether Gemini models via Vertex AI can reliably detect tampered Thai financial/employment documents (payslips, หนังสือรับรอง). Goal is to inform the PL-MOU automation pipeline design at Infinitas KT.

---

## Session 1 — 2026-06-09

### Environment Setup
- Confirmed `gcloud` SDK (v571) already installed and authenticated as `phol.w@infinitaskt.com`
- GCP project: `infinitas-ds-ai-poc`, location: `us-central1`
- ADC credentials already present at `~/.config/gcloud/application_default_credentials.json`
- Vertex AI API confirmed enabled (dashboard showing traffic graphs)
- Installed `google-cloud-aiplatform`, `google-cloud-storage`, `google-genai` into `~/miniforge3/envs/ds`
- Smoke tested: `vertexai.init()` OK; `gemini-2.5-flash` and `gemini-2.5-pro` confirmed working

### Key Discovery
- `vertexai.generative_models` module is **deprecated as of June 2025** — use `google-genai` SDK with `vertexai=True`
- Model IDs `gemini-1.5-*` and `gemini-2.0-flash` return 404 in this project — only `gemini-2.5-*` confirmed available
- Correct pattern: `client.models.generate_content(model=..., contents=[prompt, PIL.Image])`

### Skeleton Built
```
systematic-llm-test/
├── config.py                  # GCP config, model list, paths, rate limit constants
├── evaluate.py                # Main eval loop — images × models × prompts × iterations
├── labels/manifest.csv        # Ground truth (headers only, populate as data is created)
├── prompts/library.py         # 5 versioned prompts: zero-shot, CoT, structured, stamp probe, text probe
├── data_prep/
│   ├── tamper.py              # STUB — text replacement, stamp overlay, deletion
│   └── augment.py             # PARTIAL — rotate/brightness/noise/blur done; tilt + scan degradation are stubs
├── utils/
│   ├── schema.py              # ImageRecord + EvalResult dataclasses
│   ├── auth.py                # Singleton Vertex AI client
│   └── rate_limit.py          # Retry decorator (exponential backoff, 3 attempts)
├── rationale.md               # Why every structural decision was made
└── workflow.html              # Visual 5-phase workflow diagram
```

### Design Decisions Locked In
- Loop order: `images → models → prompts → iterations` (crash-safe: complete rows for processed images)
- Output format: `.jsonl` — one row per result, flushed immediately, crash-safe
- Ground truth embedded in every result row — no joins needed for analysis
- `N_ITERATIONS = 3` to measure model consistency (non-deterministic at default temperature)
- Rate limit enforced as `min_gap = 60 / RPM` — sleeps only when calls finish faster than quota allows

### Session 1 — Files Added
```
systematic-llm-test/
├── config.py                  # GCP config, model list, paths, rate limit constants
├── evaluate.py                # Main eval loop — images × models × prompts × iterations
├── score.py                   # Scoring: majority vote → precision/recall/F1 → MLflow logging
├── labels/manifest.csv        # Ground truth (headers only, populate as data is created)
├── prompts/library.py         # 5 versioned prompts: zero-shot, CoT, structured, stamp probe, text probe
├── data_prep/
│   ├── tamper.py              # STUB — text replacement, stamp overlay, deletion
│   └── augment.py             # PARTIAL — rotate/brightness/noise/blur done; tilt + scan degradation stubs
├── utils/
│   ├── schema.py              # ImageRecord + EvalResult dataclasses
│   ├── auth.py                # Singleton Vertex AI client
│   └── rate_limit.py          # Retry decorator (exponential backoff, 3 attempts)
├── rationale.md               # Why every structural decision was made
└── workflow.html              # Visual 5-phase workflow diagram
```

---

## Session 2 — 2026-06-09 (continued)

### Prompt Optimisation Strategy Added
Decided to treat prompt wording as a test variable with the same rigour as model selection. Workflow:
1. Fix a small **dev set** of 10–15 images (tagged `split=dev` in manifest) — never change this during prompt iteration
2. Iterate: edit prompt in `library.py` (bump version) → run `evaluate.py` on dev split → run `score.py` → compare recall in MLflow UI
3. Primary metric is **recall** (false negatives = missed fraud = worse outcome than false alarms)
4. Once a prompt achieves recall ≥ 0.9 on high-severity dev cases, expand to full test set

### Tooling Decision: MLflow + Git (no new installs)
Considered: Promptfoo (needs Node.js), LangSmith (hosted SaaS — data policy risk), DSPy (overkill for now).
Chose MLflow because it is already installed in the `ds` env, runs fully local, and handles experiment comparison out of the box.

### Changes Made
- `config.py` — added `MLFLOW_EXPERIMENT` and `MLFLOW_TRACKING_URI` (stored under `mlruns/` in project dir)
- `evaluate.py` — wrapped each run in `mlflow.start_run()`. Logs params (models, prompts, n_images, split), operational metrics (total_calls, error_count, avg_latency_s), and the `.jsonl` as an artifact
- `evaluate.py` — added `split` filter param: pass `split="dev"` during prompt iteration, `split=None` for a full run
- `utils/schema.py` — added `split: Split` field to `ImageRecord` (default `"dev"`)
- `labels/manifest.csv` — added `split` column header
- `score.py` (new) — loads `.jsonl`, majority-votes across iterations, computes precision/recall/F1/consistency per (model × prompt_id), logs each combo as a separate MLflow run for side-by-side comparison. `slice_metrics()` is a stub for future per-severity/doc-type breakdown.

### How to Run
```bash
# 1. Collect results
python evaluate.py                        # dev split, all models + prompts

# 2. Score and log to MLflow
python score.py results/eval_<ts>.jsonl

# 3. View comparison dashboard
mlflow ui --backend-store-uri mlruns/
# → open http://localhost:5000
```

---

## To Do — Next Session

### Immediate
- [ ] Add first real documents to `data/raw/` and populate `manifest.csv` rows (including `split` column) to run end-to-end pipeline test
- [ ] Decide on tampering implementation approach (PIL draw vs OCR-guided vs OpenCV inpainting) before filling `data_prep/tamper.py`

### To Revisit
- [ ] **Prompt ordering / session bleed concern** — each `generate_content()` call is stateless today (no chat session object). But worth one controlled test: call same image twice in rapid succession with contradictory prompts and confirm response 2 is unaffected by response 1. Document result here.
- [ ] Implement `slice_metrics()` in `score.py` — breakdown by severity, doc_type, image_quality once enough data exists
- [ ] Implement `tilt()` in `augment.py` (needs OpenCV `getPerspectiveTransform`)
- [ ] Implement `apply_scan_degradation()` — scanner shadow, uneven lighting, JPEG compression artefacts
- [ ] Consider `argparse` for `evaluate.py` and `score.py` when running from CLI
- [ ] Check if Node.js is available — if so, evaluate Promptfoo as a complement to MLflow for more structured prompt test-case management
