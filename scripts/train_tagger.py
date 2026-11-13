"""Train a token-level injection tagger and evaluate it on several held-out sets.

Long documents are cut into windows. A document's score is the highest injection probability of any
token in any window; the alarm threshold is fitted on a separate benign set at a fixed false-positive rate.
"""

import argparse
import json
import random
from pathlib import Path

import numpy as np
import torch
from sklearn.metrics import roc_auc_score
from transformers import (
    AutoModelForTokenClassification,
    AutoTokenizer,
    DataCollatorForTokenClassification,
    Trainer,
    TrainingArguments,
)


def read(path: str | Path, limit: int | None = None, seed: int = 0) -> list[dict]:
    rows = [json.loads(line) for line in Path(path).read_text().splitlines() if line.strip()]
    if limit and len(rows) > limit:
        rows = random.Random(seed).sample(rows, limit)
    return rows


def windows(rows: list[dict], tokenizer, max_len: int, stride: int, max_windows: int) -> tuple[list[dict], list[int]]:
    """Return window features and, for each window, the index of the document it came from."""
    enc = tokenizer([r["text"] for r in rows], truncation=True, max_length=max_len, stride=stride,
                    return_overflowing_tokens=True, return_offsets_mapping=True)
    features, owner, per_doc = [], [], {}
    for w, doc in enumerate(enc["overflow_to_sample_mapping"]):
        per_doc[doc] = per_doc.get(doc, 0) + 1
        if per_doc[doc] > max_windows:
            continue
        spans = rows[doc].get("spans") or []
        labels = [-100 if s == e else int(any(s < b and e > a for a, b in spans)) for s, e in enc["offset_mapping"][w]]
        features.append({"input_ids": enc["input_ids"][w], "attention_mask": enc["attention_mask"][w], "labels": labels})
        owner.append(doc)
    return features, owner


def evaluate(trainer: Trainer, tokenizer, rows: list[dict], args) -> dict:
    features, owner = windows(rows, tokenizer, args.max_len, 0, args.eval_windows)
    out = trainer.predict(features)
    probs = torch.softmax(torch.tensor(out.predictions).float(), dim=-1)[..., 1].numpy()
    mask = out.label_ids != -100
    probs = np.where(mask, probs, 0.0)
    owner = np.array(owner)
    scores = np.zeros(len(rows))
    np.maximum.at(scores, owner, probs.max(axis=1))
    result = {"scores": scores, "labels": np.array([int(r.get("label", bool(r.get("spans")))) for r in rows])}
    known = np.array([rows[d].get("spans") is not None for d in owner])
    if known.any():
        pred, gold = (probs > 0.5) & mask, (out.label_ids == 1) & mask
        pred, gold, m = pred[known], gold[known], mask[known]
        tp, fp, fn = (pred & gold).sum(), (pred & ~gold).sum(), (~pred & gold).sum()
        precision, recall = tp / max(tp + fp, 1), tp / max(tp + fn, 1)
        result.update(token_precision=float(precision), token_recall=float(recall),
                      token_f1=float(2 * precision * recall / max(precision + recall, 1e-9)),
                      over_removal=float(fp / max((~gold & m).sum(), 1)))
    return result


def main() -> None:
    ap = argparse.ArgumentParser()
    ap.add_argument("--train", required=True)
    ap.add_argument("--eval-dir", default="data/eval")
    ap.add_argument("--calibration", default="toucan_benign_val")
    ap.add_argument("--model", default="answerdotai/ModernBERT-base")
    ap.add_argument("--out", required=True)
    ap.add_argument("--max-len", type=int, default=1024)
    ap.add_argument("--stride", type=int, default=128)
    ap.add_argument("--train-windows", type=int, default=3)
    ap.add_argument("--eval-windows", type=int, default=6)
    ap.add_argument("--eval-limit", type=int, default=1500)
    ap.add_argument("--train-limit", type=int)
    ap.add_argument("--epochs", type=float, default=2.0)
    ap.add_argument("--max-steps", type=int, default=-1)
    ap.add_argument("--batch-size", type=int, default=16)
    ap.add_argument("--lr", type=float, default=3e-5)
    ap.add_argument("--warmup-steps", type=int, default=100)
    ap.add_argument("--seed", type=int, default=0)
    ap.add_argument("--save-model", action="store_true")
    ap.add_argument("--eval-only", help="directory of a trained model: skip training and only evaluate it")
    ap.add_argument("--num-layers", type=int, help="keep only the first K encoder layers of the pretrained model")
    args = ap.parse_args()

    source = args.eval_only or args.model
    tokenizer = AutoTokenizer.from_pretrained(source)
    model = AutoModelForTokenClassification.from_pretrained(source, num_labels=2, id2label={0: "O", 1: "INJECTION"},
                                                            label2id={"O": 0, "INJECTION": 1})
    if args.num_layers:
        model.model.layers = model.model.layers[:args.num_layers]
        model.config.num_hidden_layers = args.num_layers
    train_rows = read(args.train, args.train_limit, args.seed)
    train, _ = windows(train_rows, tokenizer, args.max_len, args.stride, args.train_windows)
    trainer = Trainer(
        model=model,
        args=TrainingArguments(
            output_dir=args.out, seed=args.seed, learning_rate=args.lr, max_steps=args.max_steps,
            num_train_epochs=args.epochs, per_device_train_batch_size=args.batch_size,
            per_device_eval_batch_size=args.batch_size * 2, logging_steps=100, save_strategy="no", report_to=[],
            warmup_steps=args.warmup_steps, weight_decay=0.01, fp16=torch.cuda.is_available(),
            dataloader_num_workers=2,
        ),
        train_dataset=train,
        data_collator=DataCollatorForTokenClassification(tokenizer),
    )
    train_seconds = 0.0
    if not args.eval_only:
        train_seconds = trainer.train().metrics.get("train_runtime", 0.0)

    out_dir = Path(args.out)
    out_dir.mkdir(parents=True, exist_ok=True)
    results, raw = {}, {}
    if args.save_model:  # saved before evaluation so that a failure there cannot lose the training
        trainer.save_model(str(out_dir / "model"))
        tokenizer.save_pretrained(str(out_dir / "model"))
    for path in sorted(p for p in Path(args.eval_dir).glob("*.jsonl") if not p.name.startswith(".")):
        res = evaluate(trainer, tokenizer, read(path, args.eval_limit, 0), args)
        raw[path.stem] = res
    benign = raw[args.calibration]["scores"]
    thresholds = {"fpr1": float(np.quantile(benign, 0.99, method="higher")), "fpr5": float(np.quantile(benign, 0.95, method="higher"))}
    for name, res in raw.items():
        y, s = res.pop("labels"), res.pop("scores")
        entry = {"n": int(len(y)), "n_injected": int(y.sum()), **{k: round(v, 4) for k, v in res.items()}}
        if 0 < y.sum() < len(y):
            entry["auroc"] = round(float(roc_auc_score(y, s)), 4)
        for key, t in thresholds.items():
            if y.sum():
                entry[f"tpr_at_{key}"] = round(float((s[y == 1] > t).mean()), 4)
            if (y == 0).any():
                entry[f"fpr_at_{key}"] = round(float((s[y == 0] > t).mean()), 4)
        results[name] = entry
        np.save(out_dir / f"scores_{name}.npy", np.stack([y, s]))
    summary = {"train": args.train, "seed": args.seed, "model": args.model, "n_train_docs": len(train_rows),
               "n_train_windows": len(train), "n_layers": len(model.model.layers), "n_params": sum(p.numel() for p in model.parameters()),
               "train_seconds": round(train_seconds, 1), "thresholds": thresholds, "results": results}
    (out_dir / "metrics.json").write_text(json.dumps(summary, indent=2))
    print(json.dumps(summary, indent=2))


if __name__ == "__main__":
    main()
