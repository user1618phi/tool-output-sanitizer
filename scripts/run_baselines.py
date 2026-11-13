"""Score released injection detectors on a labelled set and report document-level metrics.

Each model reads the text in its own window size; the document score is the max over windows.
"""

import argparse
import json
import random
import re
from pathlib import Path

import numpy as np
import torch
from sklearn.metrics import roc_auc_score
from transformers import AutoConfig, AutoModelForSequenceClassification, AutoModelForTokenClassification, AutoTokenizer

MODELS = {
    "prompt-guard-2-86m": ("meta-llama/Llama-Prompt-Guard-2-86M", "seq", 512),
    "prompt-guard-2-22m": ("meta-llama/Llama-Prompt-Guard-2-22M", "seq", 512),
    "protectai-v2": ("protectai/deberta-v3-base-prompt-injection-v2", "seq", 512),
    "horizon-base": ("Horizon-Labs/prompt-injection-guard-base", "seq", 2048),
    "horizon-small": ("Horizon-Labs/prompt-injection-guard-small", "seq", 2048),
    "wolf-defender": ("patronus-studio/wolf-defender-prompt-injection", "seq", 2048),
    "spanguard": ("Nabidnur/spanguard-span-mdistil", "token", 512),
}
POSITIVE = re.compile(r"inject|malicious|unsafe|attack|jailbreak|LABEL_1", re.I)
NEGATIVE = re.compile(r"^(O|safe|benign|LABEL_0|clean|legit.*)$", re.I)


def positive_ids(id2label: dict[int, str], kind: str) -> list[int]:
    if kind == "token":
        return [i for i, name in id2label.items() if not NEGATIVE.match(name)]
    ids = [i for i, name in id2label.items() if POSITIVE.search(name)]
    if not ids:
        raise ValueError(f"cannot tell which label means injection: {id2label}")
    return ids


def windows(ids: list[int], size: int, stride: int) -> list[list[int]]:
    if len(ids) <= size:
        return [ids]
    return [ids[i:i + size] for i in range(0, len(ids) - stride, size - stride)]


@torch.no_grad()
def score(name: str, texts: list[str], device: str, batch_size: int) -> np.ndarray:
    repo, kind, max_len = MODELS[name]
    tokenizer = AutoTokenizer.from_pretrained(repo)
    cls = AutoModelForTokenClassification if kind == "token" else AutoModelForSequenceClassification
    model = cls.from_pretrained(repo).to(device).eval()
    pos = positive_ids(AutoConfig.from_pretrained(repo).id2label, kind)
    body = max_len - 2
    first = tokenizer.cls_token_id if tokenizer.cls_token_id is not None else tokenizer.bos_token_id
    last = tokenizer.sep_token_id if tokenizer.sep_token_id is not None else tokenizer.eos_token_id
    chunks, owner = [], []
    for i, text in enumerate(texts):
        ids = tokenizer(text, add_special_tokens=False)["input_ids"]
        for w in windows(ids, body, body // 4):
            chunks.append([first, *w, last])
            owner.append(i)
    scores = np.zeros(len(texts))
    order = sorted(range(len(chunks)), key=lambda j: len(chunks[j]))
    for b in range(0, len(order), batch_size):
        idx = order[b:b + batch_size]
        batch = tokenizer.pad({"input_ids": [chunks[j] for j in idx]}, return_tensors="pt").to(device)
        probs = torch.softmax(model(**batch).logits.float(), dim=-1)[..., pos].sum(-1)
        if kind == "token":
            probs = (probs * batch["attention_mask"]).max(dim=1).values
        for j, p in zip(idx, probs.cpu().tolist()):
            scores[owner[j]] = max(scores[owner[j]], p)
    return scores


def main() -> None:
    ap = argparse.ArgumentParser()
    ap.add_argument("--eval-dir", default="data/eval")
    ap.add_argument("--calibration", default="toucan_benign_val")
    ap.add_argument("--models", nargs="+", default=list(MODELS))
    ap.add_argument("--limit", type=int, default=1500)
    ap.add_argument("--max-chars", type=int, default=60000)
    ap.add_argument("--batch-size", type=int, default=16)
    ap.add_argument("--out", default="outputs/baselines.json")
    args = ap.parse_args()

    sets = {}
    for path in sorted(Path(args.eval_dir).glob("*.jsonl")):
        rows = [json.loads(line) for line in path.read_text().splitlines() if line.strip()]
        if len(rows) > args.limit:
            rows = random.Random(0).sample(rows, args.limit)
        sets[path.stem] = rows
    device = "cuda" if torch.cuda.is_available() else "mps" if torch.backends.mps.is_available() else "cpu"

    out_path = Path(args.out)
    out_path.parent.mkdir(parents=True, exist_ok=True)
    results = json.loads(out_path.read_text()) if out_path.exists() else {}
    for name in args.models:
        if name in results and "error" not in results[name]:
            continue
        try:
            scores = {k: score(name, [r["text"][:args.max_chars] for r in rows], device, args.batch_size) for k, rows in sets.items()}
        except Exception as e:  # a gated or broken model must not stop the others
            results[name] = {"error": f"{type(e).__name__}: {str(e)[:160]}"}
            print(name, results[name], flush=True)
            continue
        # the alarm threshold comes from separate clean tool outputs, the same way as for our own models
        benign = scores[args.calibration]
        thresholds = {"fpr1": float(np.quantile(benign, 0.99, method="higher")), "default": 0.5}
        entry = {"thresholds": thresholds, "results": {}}
        for k, rows in sets.items():
            y = np.array([int(r.get("label", bool(r.get("spans")))) for r in rows])
            s_ = scores[k]
            m = {"n": int(len(y)), "n_injected": int(y.sum())}
            if 0 < y.sum() < len(y):
                m["auroc"] = round(float(roc_auc_score(y, s_)), 4)
            for key, t in thresholds.items():
                if y.sum():
                    m[f"tpr_at_{key}"] = round(float((s_[y == 1] > t).mean()), 4)
                if (y == 0).any():
                    m[f"fpr_at_{key}"] = round(float((s_[y == 0] > t).mean()), 4)
            entry["results"][k] = m
        results[name] = entry
        out_path.write_text(json.dumps(results, indent=2))
        print(name, {k: v.get("tpr_at_fpr1", v.get("fpr_at_fpr1")) for k, v in entry["results"].items()}, flush=True)


if __name__ == "__main__":
    main()
