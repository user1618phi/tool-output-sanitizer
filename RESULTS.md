# Results

Tables generated 13 Nov 2026, 13:01 from 74 training runs.

## 1. Original dataset against enriched datasets: attacks caught

Share of injected documents flagged at a 1% false-alarm threshold (BrowseSafe: AUROC ×100). Mean ± standard deviation over training runs (A0: 3, A4: 5, A1: 10, A2: 10, A3: 5, A5: 3 runs). None of these test sets was used for training.

| Training set | BIPIA test | InjecAgent | InjecAgent enh. | LLMail-Inject | BrowseSafe | Synthetic, new tools |
|---|---|---|---|---|---|---|
| A0 original (BIPIA) | 93.5 ± 7.2 | 1.2 ± 1.5 | 0.3 ± 0.3 | 4.1 ± 2.4 | 53.0 ± 2.0 | 4.6 ± 1.9 |
| A4 + N attacks, no twins | 97.9 ± 1.3 | 62.1 ± 17.2 | 97.7 ± 3.2 | 65.4 ± 19.6 | 68.1 ± 1.7 | 99.2 ± 0.6 |
| A1 + N unpaired twins | 98.9 ± 0.8 | 79.5 ± 6.5 | 95.7 ± 4.3 | 77.9 ± 12.6 | 76.9 ± 1.8 | 98.1 ± 0.6 |
| A2 + N paired twins | 98.4 ± 0.9 | 80.4 ± 3.9 | 97.2 ± 3.0 | 73.8 ± 14.1 | 77.1 ± 1.5 | 98.2 ± 0.5 |
| A3 + 2N unpaired twins | 98.9 ± 0.8 | 87.0 ± 3.8 | 99.0 ± 1.3 | 84.5 ± 5.0 | 77.6 ± 1.2 | 99.2 ± 0.2 |
| A5 + 2N paired twins | 97.6 ± 1.8 | 79.6 ± 1.7 | 99.1 ± 0.9 | 80.5 ± 3.6 | 78.1 ± 1.6 | 98.6 ± 0.4 |

On InjecAgent, paired data (A2) is 0.9 points higher (inside the spread between runs) than unpaired data of the same size (A1); against the original dataset (A0) it is 79.1 points higher.

## 2. False alarms and text removed by mistake

Share of clean documents flagged at the same threshold, and share of clean tokens the sanitizer would delete. Lower is better.

| Training set | Clean tool outputs | NotInject | BIPIA clean | Synthetic test, harmless | Tokens removed: clean outputs | Tokens removed: NotInject |
|---|---|---|---|---|---|---|
| A0 original (BIPIA) | 1.1 ± 0.8 | 12.1 ± 10.4 | 0.5 ± 0.5 | 2.0 ± 1.0 | 0.7 ± 0.5 | 48.8 ± 6.5 |
| A4 + N attacks, no twins | 2.2 ± 1.1 | 52.3 ± 20.8 | 2.1 ± 0.9 | 49.7 ± 2.0 | 0.3 ± 0.1 | 46.9 ± 10.0 |
| A1 + N unpaired twins | 1.3 ± 0.4 | 61.8 ± 12.5 | 2.6 ± 0.8 | 6.9 ± 1.0 | 0.1 ± 0.0 | 26.0 ± 6.1 |
| A2 + N paired twins | 1.0 ± 0.6 | 68.5 ± 9.6 | 3.0 ± 0.6 | 6.4 ± 1.4 | 0.0 ± 0.0 | 33.0 ± 11.4 |
| A3 + 2N unpaired twins | 1.9 ± 0.5 | 67.9 ± 9.6 | 3.5 ± 1.1 | 7.8 ± 1.1 | 0.0 ± 0.0 | 26.9 ± 10.9 |
| A5 + 2N paired twins | 0.4 ± 0.1 | 66.6 ± 7.5 | 3.0 ± 0.9 | 4.2 ± 0.9 | 0.0 ± 0.0 | 34.1 ± 7.2 |

## 3. How exactly the injected span is cut out

Token-level F1 between the predicted and the true injected span (threshold 0.5). Higher is better.

| Training set | BIPIA test | InjecAgent | InjecAgent enh. | Synthetic, new tools |
|---|---|---|---|---|
| A0 original (BIPIA) | 91.6 ± 2.1 | 21.0 ± 20.0 | 17.0 ± 26.2 | 15.6 ± 6.4 |
| A4 + N attacks, no twins | 94.2 ± 1.7 | 78.4 ± 4.9 | 93.5 ± 2.4 | 67.3 ± 1.3 |
| A1 + N unpaired twins | 94.1 ± 1.7 | 84.1 ± 4.0 | 91.0 ± 5.6 | 92.8 ± 1.0 |
| A2 + N paired twins | 92.2 ± 2.3 | 85.3 ± 3.7 | 92.5 ± 2.5 | 93.6 ± 0.3 |
| A3 + 2N unpaired twins | 93.1 ± 1.4 | 85.8 ± 4.7 | 93.3 ± 3.5 | 94.9 ± 0.2 |
| A5 + 2N paired twins | 92.5 ± 1.5 | 85.5 ± 2.9 | 95.0 ± 2.5 | 95.4 ± 0.5 |

## 4. Hypothesis 1: do the harmless twins matter? Attacks only against attacks with twins

A4 is A1 with every twin taken out of its tool output: same attacks, same tool outputs, same size, but no harmless twins.

| Measure | A4 + N attacks, no twins | A1 + N unpaired twins | Difference | p | Reading |
|---|---|---|---|---|---|
| InjecAgent, attacks caught ↑ | 62.1 ± 17.2 | 79.5 ± 6.5 | +17.3 | 0.086 | no clear difference |
| InjecAgent enh., attacks caught ↑ | 97.7 ± 3.2 | 95.7 ± 4.3 | -2.0 | 0.333 | no clear difference |
| LLMail-Inject, attacks caught ↑ | 65.4 ± 19.6 | 77.9 ± 12.6 | +12.5 | 0.245 | no clear difference |
| BrowseSafe AUROC ↑ | 68.1 ± 1.7 | 76.9 ± 1.8 | +8.9 | 0.000 | A1 better |
| Synthetic (new tools), attacks caught ↑ | 99.2 ± 0.6 | 98.1 ± 0.6 | -1.1 | 0.008 | A4 better |
| Attack vs its twin, AUROC ↑ | 69.3 ± 4.9 | 98.9 ± 0.2 | +29.6 | 0.000 | A1 better |
| Harmless twins flagged ↓ | 93.9 ± 3.1 | 12.0 ± 1.8 | -81.9 | 0.000 | A1 better |
| Clean tool outputs flagged ↓ | 2.2 ± 1.1 | 1.3 ± 0.4 | -0.9 | 0.146 | no clear difference |
| NotInject flagged ↓ | 52.3 ± 20.8 | 61.8 ± 12.5 | +9.5 | 0.385 | no clear difference |
| InjecAgent, span F1 ↑ | 78.4 ± 4.9 | 84.1 ± 4.0 | +5.7 | 0.061 | no clear difference |
| Synthetic, span F1 ↑ | 67.3 ± 1.3 | 92.8 ± 1.0 | +25.6 | 0.000 | A1 better |

With 5 and 10 training runs, 4 of 11 measures favour A1 and 1 favour A4 at p < 0.05 (Welch t-test, not corrected for the number of measures); the rest show no clear difference.

## 5. Hypothesis 2: does pairing matter? Unpaired against paired twins

A1 and A2 contain exactly the same attack and twin texts and the same number of examples. In A2 each twin sits in the same tool output and position as its attack; in A1 it sits in a different tool output. ↑ higher is better, ↓ lower is better.

| Measure | A1 + N unpaired twins | A2 + N paired twins | Difference | p | Reading |
|---|---|---|---|---|---|
| InjecAgent, attacks caught ↑ | 79.5 ± 6.5 | 80.4 ± 3.9 | +0.9 | 0.717 | no clear difference |
| InjecAgent enh., attacks caught ↑ | 95.7 ± 4.3 | 97.2 ± 3.0 | +1.5 | 0.364 | no clear difference |
| LLMail-Inject, attacks caught ↑ | 77.9 ± 12.6 | 73.8 ± 14.1 | -4.1 | 0.506 | no clear difference |
| BrowseSafe AUROC ↑ | 76.9 ± 1.8 | 77.1 ± 1.5 | +0.2 | 0.775 | no clear difference |
| Synthetic (new tools), attacks caught ↑ | 98.1 ± 0.6 | 98.2 ± 0.5 | +0.1 | 0.740 | no clear difference |
| Attack vs its twin, AUROC ↑ | 98.9 ± 0.2 | 99.0 ± 0.1 | +0.1 | 0.098 | no clear difference |
| Harmless twins flagged ↓ | 12.0 ± 1.8 | 11.2 ± 2.3 | -0.8 | 0.383 | no clear difference |
| Clean tool outputs flagged ↓ | 1.3 ± 0.4 | 1.0 ± 0.6 | -0.3 | 0.156 | no clear difference |
| NotInject flagged ↓ | 61.8 ± 12.5 | 68.5 ± 9.6 | +6.7 | 0.197 | no clear difference |
| InjecAgent, span F1 ↑ | 84.1 ± 4.0 | 85.3 ± 3.7 | +1.2 | 0.489 | no clear difference |
| Synthetic, span F1 ↑ | 92.8 ± 1.0 | 93.6 ± 0.3 | +0.7 | 0.040 | A2 better |

With 10 and 10 training runs, 1 of 11 measures favour A2 and 0 favour A1 at p < 0.05 (Welch t-test, not corrected for the number of measures); the rest show no clear difference.

## 6. Hypothesis 2 at twice the data: 2N unpaired against 2N paired

A3 and A5 again contain the same texts; A5 places every twin with its attack. An independent repeat of the comparison above.

| Measure | A3 + 2N unpaired twins | A5 + 2N paired twins | Difference | p | Reading |
|---|---|---|---|---|---|
| InjecAgent, attacks caught ↑ | 87.0 ± 3.8 | 79.6 ± 1.7 | -7.4 | 0.010 | A3 better |
| InjecAgent enh., attacks caught ↑ | 99.0 ± 1.3 | 99.1 ± 0.9 | +0.1 | 0.881 | no clear difference |
| LLMail-Inject, attacks caught ↑ | 84.5 ± 5.0 | 80.5 ± 3.6 | -4.0 | 0.234 | no clear difference |
| BrowseSafe AUROC ↑ | 77.6 ± 1.2 | 78.1 ± 1.6 | +0.5 | 0.675 | no clear difference |
| Synthetic (new tools), attacks caught ↑ | 99.2 ± 0.2 | 98.6 ± 0.4 | -0.5 | 0.127 | no clear difference |
| Attack vs its twin, AUROC ↑ | 99.4 ± 0.1 | 99.5 ± 0.0 | +0.1 | 0.022 | A5 better |
| Harmless twins flagged ↓ | 13.2 ± 2.1 | 7.7 ± 1.7 | -5.5 | 0.009 | A5 better |
| Clean tool outputs flagged ↓ | 1.9 ± 0.5 | 0.4 ± 0.1 | -1.5 | 0.003 | A5 better |
| NotInject flagged ↓ | 67.9 ± 9.6 | 66.6 ± 7.5 | -1.3 | 0.835 | no clear difference |
| InjecAgent, span F1 ↑ | 85.8 ± 4.7 | 85.5 ± 2.9 | -0.3 | 0.919 | no clear difference |
| Synthetic, span F1 ↑ | 94.9 ± 0.2 | 95.4 ± 0.5 | +0.4 | 0.253 | no clear difference |

With 5 and 3 training runs, 3 of 11 measures favour A5 and 1 favour A3 at p < 0.05 (Welch t-test, not corrected for the number of measures); the rest show no clear difference.

## 7. Generator fingerprint: does the model depend on which LLM wrote its training data?

For each generator: a model trained on data from all seven generators against a model that never saw this generator, tested on that generator's attacks placed in tools unseen in training. Both models get the same amount of data.

| Held-out generator | Caught, generator seen | Caught, generator unseen | Span F1, seen | Span F1, unseen |
|---|---|---|---|---|
| alemllm | 95.1 ± 0.5 | 84.0 ± 6.0 | 89.9 ± 0.6 | 77.9 ± 2.3 |
| deepseek | 98.9 ± 0.5 | 99.6 ± 0.5 | 97.1 ± 0.0 | 96.8 ± 0.3 |
| gemma | 99.2 ± 0.0 | 99.2 ± 0.0 | 96.4 ± 0.5 | 94.0 ± 1.1 |
| glm | 98.8 ± 0.0 | 98.8 ± 0.8 | 95.5 ± 0.5 | 92.9 ± 0.3 |
| gptoss | 98.1 ± 0.0 | 97.8 ± 1.3 | 97.5 ± 0.2 | 96.8 ± 1.0 |
| kimi | 99.6 ± 0.5 | 98.2 ± 0.5 | 93.2 ± 1.2 | 91.6 ± 0.7 |
| qwen | 99.0 ± 0.0 | 100.0 ± 0.0 | 97.3 ± 0.4 | 95.9 ± 0.7 |

Average drop in attacks caught when the generator is unseen: 1.6 points (largest 11.1, smallest -1.0). Training runs per model: 2.

## 8. Changing the model: fewer encoder layers

The same pretrained encoder cut to its first 6 or 11 of 22 layers, then trained the same way. A model-side experiment: how much depth the task needs, on the original and on the enriched dataset.

| Model | InjecAgent caught | LLMail-Inject caught | Synthetic caught | InjecAgent span F1 | Clean outputs flagged |
|---|---|---|---|---|---|
| Original (A0), 6 layers, 69M parameters, 2 min training | 0.0 ± 0.0 | 0.4 ± 0.6 | 1.6 ± 0.6 | 5.5 ± 0.1 | 0.3 ± 0.4 |
| Original (A0), 11 layers, 94M parameters, 3 min training | 0.0 ± 0.0 | 1.3 ± 1.2 | 2.1 ± 1.8 | 19.5 ± 17.7 | 0.6 ± 0.7 |
| Original (A0), 22 layers, 150M parameters | 1.2 ± 1.5 | 4.1 ± 2.4 | 4.6 ± 1.9 | 21.0 ± 20.0 | 1.1 ± 0.8 |
| Enriched (A2), 6 layers, 69M parameters, 4 min training | 59.8 ± 6.0 | 75.0 ± 2.1 | 93.0 ± 2.2 | 68.3 ± 0.5 | 0.3 ± 0.0 |
| Enriched (A2), 11 layers, 94M parameters, 8 min training | 66.7 ± 0.5 | 74.1 ± 0.3 | 96.8 ± 0.6 | 71.1 ± 1.4 | 1.2 ± 0.5 |
| Enriched (A2), 22 layers, 150M parameters, 15 min training | 80.4 ± 3.9 | 73.8 ± 14.1 | 98.2 ± 0.5 | 85.3 ± 3.7 | 1.0 ± 0.6 |

## 9. Changing a hyperparameter: learning rate

The enriched set A2 trained with a lower and a higher learning rate, everything else unchanged (2, 10, 2 training runs).

| Setting | InjecAgent caught | LLMail-Inject caught | Synthetic caught | InjecAgent span F1 | Clean outputs flagged |
|---|---|---|---|---|---|
| Learning rate 1e-05 | 59.9 ± 1.0 | 58.3 ± 13.6 | 92.8 ± 0.8 | 72.3 ± 1.4 | 0.9 ± 0.5 |
| Learning rate 3e-05 (used everywhere else) | 80.4 ± 3.9 | 73.8 ± 14.1 | 98.2 ± 0.5 | 85.3 ± 3.7 | 1.0 ± 0.6 |
| Learning rate 0.0001 | 82.9 ± 3.6 | 79.7 ± 3.3 | 98.6 ± 0.1 | 84.7 ± 5.4 | 1.3 ± 1.3 |

## 10. Product model: adding harmless instruction-like documents

The enriched set A2 plus whole documents that read like instructions but are legitimate (requests to an assistant, how-to text, customer requests), written by four LLMs without using any benchmark text. NotInject is a held-out benchmark; 'harmless instructions' is the held-out fifth of the new documents. The planted-command columns use held-out instruction documents with a synthetic attack or twin inserted; the last column uses held-out attacks that name no outside destination. Cells without a spread come from one saved model. Training runs: A2 10, P1 3, P2 3, P3 3, P4 1.

| Training set | InjecAgent caught | InjecAgent enh. caught | LLMail-Inject caught | BrowseSafe AUROC | Synthetic caught | InjecAgent span F1 | Clean outputs flagged | NotInject flagged | Harmless instructions flagged | Command planted in an instruction document: caught | Instruction documents (clean or with twin) flagged | Attack with no outside destination: caught |
|---|---|---|---|---|---|---|---|---|---|---|---|---|
| A2 + N paired twins | 80.4 ± 3.9 | 97.2 ± 3.0 | 73.8 ± 14.1 | 77.1 ± 1.5 | 98.2 ± 0.5 | 85.3 ± 3.7 | 1.0 ± 0.6 | 68.5 ± 9.6 | 42.3 | 98.5 | 23.7 | 92.0 |
| P1 = A2 + 1,246 harmless instruction documents | 79.5 ± 6.5 | 96.9 ± 3.5 | 72.6 ± 5.6 | 78.0 ± 0.4 | 98.5 ± 0.5 | 83.1 ± 3.8 | 1.0 ± 0.6 | 9.8 ± 7.5 | 0.1 ± 0.1 | – | – | – |
| P2 = A2 + 2,685 harmless instruction documents | 80.2 ± 4.1 | 98.4 ± 1.5 | 70.1 ± 8.2 | 78.3 ± 0.8 | 98.3 ± 0.5 | 84.8 ± 4.7 | 1.5 ± 0.8 | 6.8 ± 0.6 | 0.0 ± 0.0 | 92.3 | 2.1 | – |
| P3 = P2 + attacks and twins inside instruction documents | 72.9 ± 0.9 | 97.7 ± 1.6 | 78.1 ± 2.4 | 79.1 ± 2.2 | 98.6 ± 0.2 | 80.3 ± 4.0 | 0.5 ± 0.2 | 2.8 ± 0.8 | 0.3 ± 0.1 | 99.3 ± 0.0 | 7.5 ± 1.0 | 94.3 |
| P4 = P3 + attacks that work through the normal reply | 77.6 | 99.7 | 69.2 | 78.5 | 99.2 | 82.5 | 0.9 | 6.2 | 0.1 | 99.6 | 5.7 | 98.2 |

P1 vs A2, InjecAgent caught: -0.9 points, p = 0.841; P1 vs A2, LLMail-Inject caught: -1.2 points, p = 0.838; P1 vs A2, NotInject flagged: -58.7 points, p = 0.000; P2 vs A2, InjecAgent caught: -0.1 points, p = 0.960; P2 vs A2, LLMail-Inject caught: -3.7 points, p = 0.589; P2 vs A2, NotInject flagged: -61.7 points, p = 0.000; P3 vs A2, InjecAgent caught: -7.5 points, p = 0.000; P3 vs A2, LLMail-Inject caught: +4.3 points, p = 0.381; P3 vs A2, NotInject flagged: -65.7 points, p = 0.000.

## 11. Released open detectors on the same test sets

Same threshold rule for every model: 1% false alarms on separate clean tool outputs. Released models were trained on other data, some of which may overlap with these test sets, so this is context, not a controlled comparison.

| Model | BIPIA test | InjecAgent | InjecAgent enh. | LLMail-Inject | BrowseSafe AUROC | False alarms: clean outputs | False alarms: NotInject |
|---|---|---|---|---|---|---|---|
| Prompt Guard 2 (86M) | 0.9 | 1.8 | 100.0 | 22.2 | 71.8 | 2.4 | 6.8 |
| Prompt Guard 2 (22M) | 0.0 | 0.0 | 2.5 | 8.1 | 63.4 | 1.4 | 0.6 |
| ProtectAI v2 | 14.2 | 7.4 | 92.7 | 13.2 | 66.6 | 1.4 | 20.6 |
| Horizon-Labs base | 33.1 | 42.2 | 100.0 | 100.0 | 75.3 | 3.9 | 1.5 |
| Horizon-Labs small | 24.5 | 50.4 | 100.0 | 100.0 | 78.5 | 1.8 | 0.0 |
| Wolf Defender | 87.2 | 74.8 | 99.7 | 99.2 | 90.3 | 3.9 | 2.9 |
| SpanGuard | 3.8 | 0.0 | 4.4 | 1.3 | 58.2 | 1.4 | 0.0 |
| Ours, A0 original (BIPIA) | 93.5 ± 7.2 | 1.2 ± 1.5 | 0.3 ± 0.3 | 4.1 ± 2.4 | 53.0 ± 2.0 | 1.1 ± 0.8 | 12.1 ± 10.4 |
| Ours, A2 + N paired twins | 98.4 ± 0.9 | 80.4 ± 3.9 | 97.2 ± 3.0 | 73.8 ± 14.1 | 77.1 ± 1.5 | 1.0 ± 0.6 | 68.5 ± 9.6 |
| Ours, product model P3 | 97.9 ± 0.6 | 72.9 ± 0.9 | 97.7 ± 1.6 | 78.1 ± 2.4 | 79.1 ± 2.2 | 0.5 ± 0.2 | 2.8 ± 0.8 |

## 12. Synthetic data: what each generator produced

Each LLM wrote an attack and a harmless twin for a real tool output. A judge model labelled both texts blind; a pair is accepted only if the attack is judged hijacking and the twin harmless.

| Generator | Pairs requested | Accepted | Acceptance | Rejected by judge | Unreadable answer | Refused | Words shared with twin |
|---|---|---|---|---|---|---|---|
| alemllm | 900 | 689 | 77% | 164 | 26 | 0 | 19% |
| deepseek | 900 | 607 | 67% | 230 | 36 | 0 | 43% |
| gemma | 2080 | 697 | 34% | 1324 | 39 | 0 | 64% |
| glm | 900 | 769 | 85% | 75 | 47 | 0 | 37% |
| gptoss | 1160 | 721 | 62% | 379 | 25 | 32 | 39% |
| kimi | 1160 | 550 | 47% | 362 | 239 | 8 | 55% |
| qwen | 1160 | 452 | 39% | 471 | 66 | 0 | 41% |

4485 accepted pairs in total. Acceptance differs a lot between generators, so the judge is a real filter, and also a possible source of bias. Second opinion on 400 accepted pairs by two other LLM judges: both confirm the attack label for 98% of attacks, but both confirm 'harmless' for only 46% of twins and both call 26% of twins hijacking. Where a harmless instruction ends and an injection begins is not agreed even between judges.

## 13. A shortcut we found in our own data, before and after the fix

The first version of the synthetic data let a model separate attacks from twins by the presence of a link. Same recipe otherwise; the first version was trained once.

| Training data | InjecAgent | InjecAgent enh. | LLMail-Inject | BrowseSafe AUROC | False alarms: clean outputs | False alarms: NotInject |
|---|---|---|---|---|---|---|
| A2, first data version (links in 95% of attacks, 21% of twins) | 70.3 | 75.4 | 78.2 | 74.5 | 0.4 | 45.4 |
| A2, link-balanced data (53% / 46%) | 80.4 ± 3.9 | 97.2 ± 3.0 | 73.8 ± 14.1 | 77.1 ± 1.5 | 1.0 ± 0.6 | 68.5 ± 9.6 |
