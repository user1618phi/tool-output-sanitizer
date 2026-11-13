"""Command line use: sanitize a file or stdin with a trained model.

    uv run python -m tool_output_sanitizer.cli --model models/P tool_output.json
    cat page.html | uv run python -m tool_output_sanitizer.cli --model models/P --json
"""

import argparse
import json
import sys
from pathlib import Path

from tool_output_sanitizer.sanitizer import Sanitizer


def main() -> None:
    ap = argparse.ArgumentParser(description="Remove injected instructions from a tool output.")
    ap.add_argument("file", nargs="?", help="input file; stdin when omitted")
    ap.add_argument("--model", required=True, help="directory of a trained tagger")
    ap.add_argument("--threshold", type=float, default=0.5)
    ap.add_argument("--json", action="store_true", help="print spans and scores as JSON instead of the cleaned text")
    args = ap.parse_args()

    text = Path(args.file).read_text() if args.file else sys.stdin.read()
    result = Sanitizer(args.model, threshold=args.threshold).sanitize(text)
    if args.json:
        print(json.dumps({"score": result.score, "latency_ms": result.latency_ms, "sanitized": result.sanitized,
                          "spans": [vars(s) for s in result.spans]}, ensure_ascii=False, indent=2))
    else:
        print(result.sanitized)
        for span in result.spans:
            print(f"removed [{span.start}:{span.end}] score={span.score}: {span.text[:120]!r}", file=sys.stderr)


if __name__ == "__main__":
    main()
