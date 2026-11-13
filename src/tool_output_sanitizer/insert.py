"""Insert a payload into a tool output at a reproducible place and return its character span.

JSON outputs are re-serialised the same way with and without a payload, so formatting cannot give the
label away. A plan fixes the place, which lets an attack and its benign twin share it exactly.
"""

import json
import random
import re
from dataclasses import dataclass

BOUNDARY = re.compile(r"(?<=[.!?;])\s+|\n+")
MIN_LEAF = 20


@dataclass(frozen=True)
class Plan:
    leaf: int  # index of the JSON string value to edit, -1 for plain text
    mode: str  # start | middle | end
    frac: float  # which boundary to use for "middle"


def _leaves(node, out: list) -> None:
    if isinstance(node, dict):
        for key, value in node.items():
            if isinstance(value, str) and len(value) >= MIN_LEAF:
                out.append((node, key))
            else:
                _leaves(value, out)
    elif isinstance(node, list):
        for i, value in enumerate(node):
            if isinstance(value, str) and len(value) >= MIN_LEAF:
                out.append((node, i))
            else:
                _leaves(value, out)


def _parse(text: str):
    try:
        obj = json.loads(text)
    except ValueError:
        return None
    return obj if isinstance(obj, (dict, list)) else None


def canonical(text: str) -> str:
    obj = _parse(text)
    return text if obj is None else json.dumps(obj, ensure_ascii=False)


def make_plan(text: str, rng: random.Random) -> Plan:
    obj = _parse(text)
    leaves: list = []
    if obj is not None:
        _leaves(obj, leaves)
    leaf = rng.randrange(len(leaves)) if leaves else -1
    return Plan(leaf, rng.choice(("start", "middle", "end")), rng.random())


def _splice(host: str, payload: str, plan: Plan, sep: str) -> str:
    if plan.mode == "start":
        return payload + sep + host
    if plan.mode == "end":
        return host + sep + payload
    cuts = [m.end() for m in BOUNDARY.finditer(host) if 0 < m.end() < len(host)]
    cut = cuts[int(plan.frac * len(cuts))] if cuts else len(host) // 2
    return host[:cut].rstrip() + sep + payload + sep + host[cut:].lstrip()


def apply(text: str, payload: str, plan: Plan) -> tuple[str, tuple[int, int]] | None:
    """Return (new_text, (start, end)), or None if the payload cannot be located unambiguously."""
    obj = _parse(text)
    if obj is not None and plan.leaf >= 0:
        leaves: list = []
        _leaves(obj, leaves)
        if plan.leaf >= len(leaves):
            return None
        container, key = leaves[plan.leaf]
        container[key] = _splice(container[key], payload, plan, " ")
        out = json.dumps(obj, ensure_ascii=False)
        needle = json.dumps(payload, ensure_ascii=False)[1:-1]
    else:
        out = _splice(text, payload, plan, "\n")
        needle = payload
    if out.count(needle) != 1:
        return None
    start = out.index(needle)
    return out, (start, start + len(needle))
