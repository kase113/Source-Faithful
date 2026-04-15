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
| test | 54 | 7 | 12.96% | 3 | 5.56% |

## 3. Test High-Risk Examples

| sample_id | claim_id | question_type | length |
|---|---|---|---:|
| sample_0109 | sample_0109_claim_1 | 程序义务问答 | 234 |
| sample_0104 | sample_0104_claim_3 | 直接法条问答 | 233 |
| sample_0111 | sample_0111_claim_2 | 多法源联合问答 | 225 |
| sample_0118 | sample_0118_claim_1 | 条件/要件问答 | 215 |
| sample_0114 | sample_0114_claim_1 | 直接法条问答 | 198 |
| sample_0114 | sample_0114_claim_3 | 直接法条问答 | 195 |
| sample_0105 | sample_0105_claim_2 | 条件/要件问答 | 180 |

## 4. Suggested Cleanup Actions

1. Prioritize test claims with `length >= 220` for compression.
2. Convert long procedural claims into 2-3 shorter verifiable propositions.
3. Re-check citation sufficiency after rewriting.
4. Sync changes to `benchmark_*`, `annotation/claim_annotation_template.jsonl`, and `annotation/adjudication_log.jsonl`.
