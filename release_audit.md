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

- total adjudication records: **20**
- pending manual queue items: **0**

Disagreement-type counts:

| disagreement_type | count |
|---|---:|
| sufficiency_boundary | 11 |
| conflict_boundary | 1 |
| support_vs_unsupported | 1 |
| unsupported_vs_partial | 1 |
| insufficient_info_boundary | 1 |
| major_rewrite_no_label_disagreement | 5 |

## 4. Claim Style Audit (length risk)

Source: `annotation/claim_style_audit.json`

| split | claims>=180 | ratio | claims>=220 | ratio |
|---|---:|---:|---:|---:|
| train | 45 | 17.86% | 12 | 4.76% |
| dev | 9 | 16.67% | 3 | 5.56% |
| test | 7 | 12.96% | 3 | 5.56% |

## 5. Known Gaps and Next Actions

1. Some test claims remain long compared with ideal proposition-level abstraction.
2. Adjudication evidence is improving but sufficiency-boundary cases still dominate.
3. Next cleaning round should continue claim compression and metadata consistency checks while preserving citation sufficiency.
