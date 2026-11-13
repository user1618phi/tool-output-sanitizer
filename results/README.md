# Raw results

Per-run metrics behind the tables in [RESULTS.md](../RESULTS.md). One JSON file per training run: training set, seed,
thresholds and every test-set metric.

| Path | Content |
|---|---|
| `runs/<set>_s<seed>.json` | 64 runs of the research sets (A0-A5, generator hold-outs, layer and learning-rate variants) |
| `runs_product/` | 10 runs of the product sets P1-P4 |
| `runs_first_data_version/` | 2 runs on the first version of the synthetic data, for the before/after table |
| `baselines.json` | released detectors scored on the same test sets |
| `a2_benign_dev.json`, `planted_before.json` | single-run measurements of saved models on two extra test sets |
| `label_audit_judges.json` | agreement of two other LLM judges with the synthetic labels |
