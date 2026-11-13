"""Build the original dataset from BIPIA (MIT) with character-level injection spans.

BIPIA ships contexts and attack strings separately and inserts attacks at start / middle / end.
We redo the insertion ourselves so the span of the attack is known exactly.
"""

import argparse
import json
import random
import re
from pathlib import Path

BENCH = Path("data/external/BIPIA/benchmark")
POSITIONS = ("start", "middle", "end")
# BIPIA uses Punkt for the middle position; a newline/sentence-end regex avoids the nltk dependency.
BOUNDARY = re.compile(r"(?<=[.!?])\s+|\n+")


def load_jsonl(path: Path) -> list[dict]:
    return [json.loads(line) for line in path.read_text().splitlines() if line.strip()]


def as_text(value) -> str:
    return "\n".join(value) if isinstance(value, list) else str(value)


def contexts(task: str, split: str) -> list[dict]:
    rows = []
    for i, r in enumerate(load_jsonl(BENCH / task / f"{split}.jsonl")):
        if task == "code":
            user_task = (
                "I received the following error message when running my code:\n"
                f"{as_text(r['error'])}\n\nHere is my code:\n{as_text(r['code'])}\n\n"
                "Fix the bug in my code based on the Stack Overflow answer."
            )
        else:
            user_task = as_text(r["question"])
        rows.append({"ctx_id": f"{task}-{split}-{i}", "context": as_text(r["context"]), "user_task": user_task})
    return rows


def attacks(task: str, split: str) -> list[tuple[str, str]]:
    kind = "code" if task == "code" else "text"
    data = json.loads((BENCH / f"{kind}_attack_{split}.json").read_text())
    return [(category, s) for category, strings in data.items() for s in strings]


def insert(context: str, attack: str, position: str, rng: random.Random) -> tuple[str, int]:
    if position == "start":
        return f"{attack}\n{context}", 0
    if position == "end":
        return f"{context}\n{attack}", len(context) + 1
    cuts = [m.end() for m in BOUNDARY.finditer(context) if 0 < m.end() < len(context)]
    cut = rng.choice(cuts) if cuts else len(context) // 2
    return f"{context[:cut]}\n{attack}\n{context[cut:]}", cut + 1


def build(split: str, per_context: dict[str, int], seed: int) -> list[dict]:
    rng = random.Random(seed)
    out = []
    for task in ("email", "table", "code"):
        pool = [(c, a, p) for c, a in attacks(task, split) for p in POSITIONS]
        for ctx in contexts(task, split):
            base = {"task": task, "split": split, "user_task": ctx["user_task"], "source": "bipia"}
            out.append({**base, "id": f"{ctx['ctx_id']}-clean", "text": ctx["context"], "spans": [],
                        "attack_category": None, "position": None})
            for n, (category, attack, position) in enumerate(rng.sample(pool, min(per_context[task], len(pool)))):
                text, start = insert(ctx["context"], attack, position, rng)
                end = start + len(attack)
                assert text[start:end] == attack
                out.append({**base, "id": f"{ctx['ctx_id']}-{n}", "text": text, "spans": [[start, end]],
                            "attack_category": category, "position": position})
    return out


def main() -> None:
    ap = argparse.ArgumentParser()
    ap.add_argument("--out", default="data/bipia")
    ap.add_argument("--seed", type=int, default=0)
    ap.add_argument("--email", type=int, default=40)
    ap.add_argument("--table", type=int, default=4)
    ap.add_argument("--code", type=int, default=40)
    args = ap.parse_args()

    out_dir = Path(args.out)
    out_dir.mkdir(parents=True, exist_ok=True)
    per_context = {"email": args.email, "table": args.table, "code": args.code}
    for split in ("train", "test"):
        rows = build(split, per_context, args.seed)
        (out_dir / f"{split}.jsonl").write_text("\n".join(json.dumps(r, ensure_ascii=False) for r in rows) + "\n")
        poisoned = sum(bool(r["spans"]) for r in rows)
        cats = {r["attack_category"] for r in rows if r["attack_category"]}
        lens = sorted(len(r["text"]) for r in rows)
        print(f"{split}: {len(rows)} rows, {poisoned} poisoned, {len(rows) - poisoned} clean, "
              f"{len(cats)} attack categories, median chars {lens[len(lens) // 2]}, max {lens[-1]}")
    train_cats = {r["attack_category"] for r in load_jsonl(out_dir / "train.jsonl")} - {None}
    test_cats = {r["attack_category"] for r in load_jsonl(out_dir / "test.jsonl")} - {None}
    print("attack categories shared between train and test:", sorted(train_cats & test_cats))


if __name__ == "__main__":
    main()
