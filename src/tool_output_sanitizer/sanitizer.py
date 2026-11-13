"""Find and remove injected instructions in a tool output with a trained token tagger."""

import re
import time
from dataclasses import dataclass
from pathlib import Path

import torch
from transformers import AutoModelForTokenClassification, AutoTokenizer


SENTENCE_END = re.compile(r'[.!?](?=["\'\s\\]|$)|\n')
MAX_GROW = 160


def grow_to_sentence(text: str, start: int, end: int) -> tuple[int, int]:
    """Widen a span to the sentence it sits in, so that half a sentence is never left behind."""
    left = [m.end() for m in SENTENCE_END.finditer(text, max(0, start - MAX_GROW), start)]
    quote = text.rfind('"', max(0, start - MAX_GROW), start)
    new_start = max(left[-1] if left else -1, quote + 1 if quote >= 0 else -1)
    if new_start >= 0:
        start = new_start + (len(text[new_start:start]) - len(text[new_start:start].lstrip()))
    if text[end - 1:end] == '"' and end - 1 > start:
        end -= 1  # never swallow the quote that closes a JSON string
    if text[end - 1:end] not in ".!?\n":  # the span stops mid-sentence: finish the sentence
        right = SENTENCE_END.search(text, end, min(len(text), end + MAX_GROW))
        quote = text.find('"', end, min(len(text), end + MAX_GROW))
        if right and (quote < 0 or right.end() <= quote):
            end = right.end()
        elif quote >= 0:
            end = quote
    return start, end


@dataclass
class Span:
    start: int
    end: int
    score: float
    text: str


@dataclass
class Result:
    spans: list[Span]
    score: float
    sanitized: str
    latency_ms: float


class Sanitizer:
    def __init__(self, model_dir: str | Path, threshold: float = 0.5, max_len: int = 1024, device: str | None = None):
        self.tokenizer = AutoTokenizer.from_pretrained(model_dir)
        self.model = AutoModelForTokenClassification.from_pretrained(model_dir).eval()
        self.device = device or ("cuda" if torch.cuda.is_available() else "mps" if torch.backends.mps.is_available() else "cpu")
        self.model.to(self.device)
        self.threshold = threshold
        self.max_len = max_len

    @torch.no_grad()
    def token_scores(self, text: str) -> list[tuple[int, int, float]]:
        """Return (char_start, char_end, injection probability) for every token."""
        enc = self.tokenizer(text, truncation=True, max_length=self.max_len, stride=self.max_len // 8,
                             return_overflowing_tokens=True, return_offsets_mapping=True, padding=True, return_tensors="pt")
        logits = self.model(input_ids=enc["input_ids"].to(self.device), attention_mask=enc["attention_mask"].to(self.device)).logits
        probs = torch.softmax(logits.float(), dim=-1)[..., 1].cpu()
        best: dict[tuple[int, int], float] = {}
        for w in range(probs.shape[0]):
            for (start, end), mask, p in zip(enc["offset_mapping"][w].tolist(), enc["attention_mask"][w].tolist(), probs[w].tolist()):
                if mask and end > start:
                    best[(start, end)] = max(best.get((start, end), 0.0), p)  # overlapping windows: keep the higher score
        return sorted((s, e, p) for (s, e), p in best.items())

    def sanitize(self, text: str, marker: str = "[removed by sanitizer]", max_gap: int = 12, min_chars: int = 8) -> Result:
        started = time.perf_counter()
        tokens = self.token_scores(text)
        spans: list[list] = []
        for start, end, p in tokens:
            if p <= self.threshold:
                continue
            if spans and start - spans[-1][1] <= max_gap:  # bridge short gaps so one injection stays one span
                spans[-1][1] = end
                spans[-1][2] = max(spans[-1][2], p)
            else:
                spans.append([start, end, p])
        kept: list[Span] = []
        for s, e, p in spans:
            if e - s < min_chars:
                continue
            s, e = grow_to_sentence(text, s, e)
            if kept and s <= kept[-1].end:  # two hits in one sentence become one span
                s, p = kept[-1].start, max(p, kept[-1].score)
                kept.pop()
            kept.append(Span(s, e, round(p, 4), text[s:e]))
        out, cursor = [], 0
        for span in kept:
            out += [text[cursor:span.start], marker]
            cursor = span.end
        out.append(text[cursor:])
        score = max((p for _, _, p in tokens), default=0.0)
        return Result(kept, round(score, 4), "".join(out), round((time.perf_counter() - started) * 1000, 1))
