"""Collect real benign tool outputs (carriers) with their user task from Toucan-1.5M (Apache-2.0).

Carriers are split by tool name so that no tool appears in more than one of train / val / test.
"""

import argparse
import hashlib
import json
import random
import time
import urllib.parse
import urllib.request
from collections import Counter
from pathlib import Path

API = "https://datasets-server.huggingface.co/rows"
DATASET = "Agent-Ark/Toucan-1.5M"


def fetch(config: str, offset: int, length: int = 100) -> list[dict]:
    query = urllib.parse.urlencode({"dataset": DATASET, "config": config, "split": "train", "offset": offset, "length": length})
    for attempt in range(5):
        try:
            with urllib.request.urlopen(f"{API}?{query}", timeout=90) as r:
                return [x["row"] for x in json.load(r)["rows"]]
        except Exception:
            time.sleep(3 * (attempt + 1))
    return []


def split_of(tool: str) -> str:
    bucket = int(hashlib.sha1(tool.encode()).hexdigest(), 16) % 10
    return "train" if bucket < 6 else "val" if bucket < 8 else "test"


def main() -> None:
    ap = argparse.ArgumentParser()
    ap.add_argument("--out", default="data/carriers/toucan.jsonl")
    ap.add_argument("--pages", type=int, default=60)
    ap.add_argument("--configs", nargs="+", default=["OSS", "Kimi-K2", "Qwen3"])
    ap.add_argument("--max-offset", type=int, default=100_000)
    ap.add_argument("--min-chars", type=int, default=300)
    ap.add_argument("--max-chars", type=int, default=6000)
    ap.add_argument("--per-tool", type=int, default=12)
    ap.add_argument("--seed", type=int, default=0)
    args = ap.parse_args()

    rng = random.Random(args.seed)
    per_tool, seen, out = Counter(), set(), []
    for page in range(args.pages):
        config = args.configs[page % len(args.configs)]
        for row in fetch(config, rng.randrange(0, args.max_offset, 100)):
            try:
                messages = json.loads(row["messages"])
            except (TypeError, ValueError):
                continue
            for m in messages:
                text, tool = m.get("content"), m.get("name") or "unknown"
                if m.get("role") not in ("function", "tool") or not isinstance(text, str):
                    continue
                digest = hashlib.sha1(text.encode()).hexdigest()
                if not args.min_chars <= len(text) <= args.max_chars or digest in seen or per_tool[tool] >= args.per_tool:
                    continue
                if text.lstrip().lower().startswith(("error", "{\"error", "traceback")):
                    continue
                seen.add(digest)
                per_tool[tool] += 1
                out.append({"id": f"toucan-{digest[:12]}", "tool": tool, "text": text,
                            "user_task": row.get("question") or "", "split": split_of(tool), "source": "toucan"})
        if page % 10 == 9:
            print(f"page {page + 1}/{args.pages}: {len(out)} carriers, {len(per_tool)} tools", flush=True)

    Path(args.out).parent.mkdir(parents=True, exist_ok=True)
    Path(args.out).write_text("\n".join(json.dumps(r, ensure_ascii=False) for r in out) + "\n")
    print("total", len(out), "| by split", dict(Counter(r["split"] for r in out)), "| tools", len(per_tool))


if __name__ == "__main__":
    main()
