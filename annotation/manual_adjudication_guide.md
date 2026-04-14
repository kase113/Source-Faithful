# Manual Adjudication Guide

## Scope

This guide defines what must be manually adjudicated after running:

`python scripts/build_dataset/expand_benchmark_pilot.py`

The auto-generator now produces more concrete claims, but some samples are still not safe as final test gold without legal review.

## Primary Queue File

- `annotation/manual_adjudication_queue.jsonl`

Each row contains:

- `sample_id`
- `split`
- `question_type`
- `authority_scope`
- `review_flags`
- `review_reason`

## Review Flags

### `generic_exception_requires_manual_review`

Meaning:

- Exception-question claim is still generic or only partially grounded.

What reviewers must do:

1. Rewrite `reference_answer` as concrete legal conclusion.
2. Split claims into verifiable propositions (no annotation-instruction style text).
3. Ensure at least one claim states the general rule and at least one states specific exception.
4. Verify `gold_citations` are sufficient for each claim (not just relevant).
5. Correct `support_label` if auto label is too broad.

### `generic_multi_authority_requires_manual_review`

Meaning:

- Multi-authority sample not yet explicit enough on division of support between two sources.

What reviewers must do:

1. Assign which claim is supported by authority A and which by authority B.
2. Add one claim explaining why single-authority citation is insufficient.
3. Check no claim overstates cross-source conclusion.
4. Confirm `requires_multi_authority=true` only where truly needed.
5. Re-check `gold_minimal_spans` for minimal sufficiency.

## Required Output Files After Adjudication

1. Update benchmark files directly:
   - `data_processed/benchmark_train.jsonl`
   - `data_processed/benchmark_dev.jsonl`
   - `data_processed/benchmark_test.jsonl`
2. Sync annotation template:
   - `annotation/claim_annotation_template.jsonl`
3. Log disagreements or major rewrites:
   - `annotation/adjudication_log.jsonl`

## Fast Acceptance Checklist

For each reviewed sample, all checks must pass:

- Claims are concrete legal propositions.
- Each claim has independently checkable citation sufficiency.
- Exception questions explicitly separate general rule vs exception.
- Multi-authority questions explicitly assign support roles by source.
- No placeholder or meta wording remains.
