# Release Audit (Current Version)

This file summarizes what was verified before release and what known risks remain.

## 1. Dataset Size

| split | samples | claims |
|---|---:|---:|
| train | 84 | 252 |
| dev | 18 | 54 |
| test | 18 | 54 |

## 2. Placeholder/Template Phrase Scan

Source: `annotation/gold_quality_audit.json`

| file | hit_count |
|---|---:|
| `data_processed/benchmark_train.jsonl` | 0 |
| `data_processed/benchmark_dev.jsonl` | 0 |
| `data_processed/benchmark_test.jsonl` | 0 |
| `annotation/claim_annotation_template.jsonl` | 0 |

Conclusion: no draft placeholder phrases were detected in the current published split files.

## 3. Manual Adjudication Status

Source: `annotation/adjudication_summary.json`

- total adjudication records: **37**
- pending manual queue items: **0**

Disagreement-type counts:

| disagreement_type | count |
|---|---:|
| sufficiency_boundary | 11 |
| conflict_boundary | 1 |
| support_vs_unsupported | 1 |
| unsupported_vs_partial | 1 |
| insufficient_info_boundary | 1 |
| major_rewrite_no_label_disagreement | 22 |

## 4. Claim Style Audit (length risk)

Source: `annotation/claim_style_audit.json`

| split | claims>=180 | ratio | claims>=220 | ratio |
|---|---:|---:|---:|---:|
| train | 45 | 17.86% | 12 | 4.76% |
| dev | 9 | 16.67% | 3 | 5.56% |
| test | 0 | 0.00% | 0 | 0.00% |

## 5. Known Gaps and Next Actions

1. Long-claim risk is now concentrated in train/dev; test has no claim >=180 chars.
2. Adjudication evidence is improving but sufficiency-boundary cases still dominate.
3. Next cleaning round should focus on train/dev claim compression and metadata consistency checks while preserving citation sufficiency.
