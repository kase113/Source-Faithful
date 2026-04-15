# Paper Section Draft (Pilot Positioning)

## Section 3 (Dataset and Annotation)

We build a source-faithful legal answering pilot benchmark with `train/dev/test=84/18/18` and `360` claim-level units. The evaluation unit is not free-form answer quality alone, but claim-level support alignment between legal propositions and authority citations.

The labeling pipeline uses "auto expansion for candidates + manual adjudication for final gold". Auto expansion is never treated as final truth. Annotation guidelines enforce: claim-level verifiability, citation sufficiency (not mere relevance), explicit handling of exceptions, and explicit support-role decomposition in multi-authority questions.

Before release, we run a placeholder scan on train/dev/test and claim template files and detect zero draft placeholder hits. We also publish adjudication logs and summary statistics for traceability. In this release, the manual queue pending count is zero.

We position this dataset as a carefully curated pilot benchmark rather than a fully mature final benchmark. Current limitations include limited scale, some long article-like claims, and still-growing adjudication evidence breadth.

## Section 5 (Evaluation and Analysis)

We report two metric layers:

1. citation-overlap metrics: macro precision/recall/F1;
2. claim-level faithfulness diagnostics: claim label accuracy, irrelevant citation rate, insufficient citation rate, overclaim rate, exception omission rate, multi-authority mismatch rate, and refusal violation count.

These diagnostics separate distinct failure modes such as "citation present but irrelevant", "citation relevant but insufficient", and "exception omitted". This avoids relying only on overlap scores.

For analysis, results should be stratified by question subtype (exception, multi-authority, temporal-sensitive), and paired with auto-vs-manual revised examples. This better supports the core contribution: source-faithful legal answering requires claim-level support adequacy, not only plausible final answers.
