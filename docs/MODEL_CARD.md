# Model card: tool-output sanitizer (product model P3, research model A2)

## What it is

A token classifier built on ModernBERT-base (149M parameters, Apache-2.0). It reads the text an AI agent received from a tool and
gives every token a probability of belonging to an injected instruction. Marked spans can then be removed before the agent sees the text.

| | |
|---|---|
| Base model | `answerdotai/ModernBERT-base`, 22 layers |
| Head | token classification, 2 labels (`O`, `INJECTION`) |
| Input | plain text, JSON, HTML or markdown; up to 1,024 tokens per window, longer inputs are windowed |
| Languages | trained on English with some multilingual synthetic examples; not evaluated on other languages |
| Training | 2 epochs, batch 16, learning rate 3e-5, AdamW, linear schedule with 100 warm-up steps, mixed precision |
| Training data, research model | set `A2`: BIPIA train (4,000 documents) + 1,246 synthetic attacks and their 1,246 harmless twins in real tool outputs + 636 clean tool outputs |
| Training data, product model | set `P3`: A2 + 2,685 harmless instruction-like documents + 1,045 attack/twin pairs placed inside such documents |
| Licence | Apache-2.0 for code and weights |

## Intended use

One layer of defence for agents that read untrusted content: flag or strip likely injected instructions in tool results, retrieved
documents, web pages and emails before they reach the agent. Meant to sit next to permission checks and sandboxing, not to replace them.

## Not intended for

- Direct user prompts or chat messages. A request that is normal from the user is, by this model's training, suspicious inside a
  tool output; on short instruction-like prompts the false-alarm rate is high.
- Use as the only safeguard for actions that are costly to undo.
- Detecting jailbreaks, harmful content or policy violations.

## Evaluation

All numbers, with the spread over training runs, are in `RESULTS.md`. The alarm threshold is fitted on separate clean tool outputs
at a 1% false-alarm rate. Test sets were not used in training: BIPIA test (attack categories unseen in training), InjecAgent,
LLMail-Inject, BrowseSafe-Bench, NotInject, clean tool outputs from tools unseen in training, and synthetic attacks on unseen tools.

For span removal the product model uses a token threshold of 0.7, chosen on a development set as the highest value that keeps span F1 within
0.2 points of the best.

## Known limits

- **Task blindness.** The model does not see what the user asked. The research model removes a legitimate request addressed to
  whoever handles the text (a customer asking support to cancel a subscription). The product model leaves it alone, and for the
  same reason lets through a planted request that only asks for data in the normal reply, with no outside destination.
- **Over-defence on instruction-like prose (research model).** A2 flags 68.5% of NotInject; the product model flags 2.8%.
- **Recall trade-off (product model).** P3 catches 72.9% of InjecAgent attacks against 80.4% for A2.
- **An attempt to close the reply-channel gap (set P4, one run, not shipped).** Adding attacks that act through the agent's
  normal reply raised detection of such attacks from 94.3% to 98.2% and InjecAgent to 77.6%, but NotInject false alarms rose to
  6.2% and LLMail-Inject fell to 69.2%. The acceptance rule fixed before the run (NotInject at most 5%) was not met.
- **Adaptive attacks not tested.** Published work shows that attacks tuned against a specific detector succeed against detectors of this kind.
- **Synthetic supervision.** Attack and twin labels were assigned by construction and checked by one judge model, not by people.
- **Generator dependence.** Accuracy can drop on attacks written in a style far from the generators seen in training (see the
  generator table in `RESULTS.md`).
- **Span boundaries.** The end of a removed span can take in a neighbouring sentence inside the same JSON string.

## Speed

Measured on an Apple M1 Pro laptop, model in memory, real tool outputs (median 930 characters): median 52 ms and 95th percentile
297 ms on the built-in GPU; median 111 ms and 95th percentile 622 ms on the CPU.

## How to run

```python
from tool_output_sanitizer.sanitizer import Sanitizer
result = Sanitizer("models/P", threshold=0.7).sanitize(text)
print(result.sanitized, result.spans)
```
