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
| test | 54 | 15 | 27.78% | 5 | 9.26% |

## 3. Test High-Risk Examples

| sample_id | claim_id | question_type | length |
|---|---|---|---:|
| sample_0110 | sample_0110_claim_2 | exception_butshu | 344 |
| sample_0109 | sample_0109_claim_1 | procedural_obligation | 234 |
| sample_0104 | sample_0104_claim_3 | direct_article_qa | 233 |
| sample_0108 | sample_0108_claim_2 | procedural_obligation | 230 |
| sample_0111 | sample_0111_claim_2 | multi_authority_joint | 225 |
| sample_0108 | sample_0108_claim_1 | procedural_obligation | 217 |
| sample_0119 | sample_0119_claim_1 | direct_article_qa | 217 |
| sample_0118 | sample_0118_claim_1 | condition_requirement | 215 |

## 4. Suggested Cleanup Actions

1. Prioritize test claims with `length >= 220` for compression.
2. Convert long procedural claims into 2-3 shorter verifiable propositions.
3. Re-check citation sufficiency after rewriting.
4. Sync changes to `benchmark_*`, `annotation/claim_annotation_template.jsonl`, and `annotation/adjudication_log.jsonl`.