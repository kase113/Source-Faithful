# Claim Length And Style Audit

This file records claim-length distribution and style risk to guide the next cleaning round.

## 1. Method

- long claim threshold: `length >= 180`
- very long claim threshold: `length >= 220`
- style risk focus: very long claims with list/enumeration-heavy legal wording

## 2. Split Statistics

| split | claims | >=180 count | >=180 ratio | >=220 count | >=220 ratio |
|---|---:|---:|---:|---:|---:|
| train | 252 | 45 | 17.86% | 12 | 4.76% |
| dev | 54 | 9 | 16.67% | 3 | 5.56% |
| test | 54 | 0 | 0.00% | 0 | 0.00% |

## 3. Test High-Risk Examples

No test claims remain at `length >= 180` in the current version.

## 4. Suggested Cleanup Actions

1. Keep train/dev as the next cleanup target because long-claim concentration is now split-heavy there.
2. Continue converting long procedural claims into 2-3 shorter verifiable propositions.
3. Re-check citation sufficiency after every rewrite.
4. Keep syncing `benchmark_*`, `annotation/claim_annotation_template.jsonl`, and `annotation/adjudication_log.jsonl`.
