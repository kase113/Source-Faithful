import argparse
import json
import re
from pathlib import Path
from itertools import permutations


def read_jsonl(path: Path):
    rows = []
    if not path.exists():
        return rows
    for line in path.read_text(encoding='utf-8').splitlines():
        line = line.strip()
        if line:
            rows.append(json.loads(line))
    return rows


def normalize_text(s: str) -> str:
    s = s or ''
    s = s.replace('（', '(').replace('）', ')')
    s = re.sub(r'\s+', '', s)
    return s


def text_similarity(a: str, b: str) -> float:
    a = normalize_text(a)
    b = normalize_text(b)
    if not a or not b:
        return 0.0
    if a in b or b in a:
        return 1.0
    sa, sb = set(a), set(b)
    return len(sa & sb) / max(1, len(sa | sb))


def load_gold_samples(data_processed: Path):
    files = [
        data_processed / 'benchmark_train.jsonl',
        data_processed / 'benchmark_dev.jsonl',
        data_processed / 'benchmark_test.jsonl',
    ]
    all_rows = []
    for f in files:
        all_rows.extend(read_jsonl(f))
    return {r.get('sample_id'): r for r in all_rows if r.get('sample_id')}


def label_from_precision_recall(prec: float, rec: float) -> str:
    if rec == 0.0:
        return 'unsupported'
    if prec == 1.0 and rec == 1.0:
        return 'supported'
    return 'partially_supported'


def citation_jaccard(a: set, b: set) -> float:
    if not a and not b:
        return 1.0
    if not a or not b:
        return 0.0
    return len(a & b) / max(1, len(a | b))


def find_best_alignment(gold_claims, pred_claims):
    """
    Align gold claims to predicted claims by maximizing a combined score:
    score = 0.7 * text_similarity + 0.3 * citation_jaccard
    Returns dict: gold_idx -> pred_idx (or None if unmatched).
    """
    n = len(gold_claims)
    m = len(pred_claims)
    if n == 0:
        return {}
    if m == 0:
        return {i: None for i in range(n)}

    score = [[0.0 for _ in range(m)] for _ in range(n)]
    for i, g in enumerate(gold_claims):
        g_text = g.get('claim_text', '')
        g_cits = set(g.get('gold_citations', []) or [])
        for j, p in enumerate(pred_claims):
            p_text = p.get('claim_text', '')
            p_cits = set(p.get('citations', []) or [])
            s_text = text_similarity(g_text, p_text)
            s_cit = citation_jaccard(g_cits, p_cits)
            score[i][j] = 0.7 * s_text + 0.3 * s_cit

    # For current benchmark, claim count per sample is small (typically <=4),
    # so exhaustive permutation is deterministic and sufficient.
    if n <= m:
        best_total = -1.0
        best_perm = None
        for perm in permutations(range(m), n):
            total = sum(score[i][perm[i]] for i in range(n))
            if total > best_total:
                best_total = total
                best_perm = perm
        return {i: best_perm[i] for i in range(n)}

    # n > m: assign each prediction to a unique gold claim, remaining unmatched
    best_total = -1.0
    best_gold_idx = None
    best_perm = None
    for gold_idx in permutations(range(n), m):
        for perm in permutations(range(m), m):
            total = sum(score[gold_idx[k]][perm[k]] for k in range(m))
            if total > best_total:
                best_total = total
                best_gold_idx = gold_idx
                best_perm = perm
    align = {i: None for i in range(n)}
    for k in range(m):
        align[best_gold_idx[k]] = best_perm[k]
    return align


def evaluate_one_sample(gold: dict, pred: dict, text_match_threshold: float):
    gold_claims = gold.get('claims', [])
    pred_claims = pred.get('claims', [])

    details = []
    macro_p = 0.0
    macro_r = 0.0
    macro_f1 = 0.0

    label_match_count = 0
    high_text_match_count = 0
    irrelevant_citation_count = 0
    insufficient_citation_count = 0
    no_citation_count = 0
    overclaim_count = 0
    temporal_mismatch_count = 0
    exception_omission_count = 0
    multi_authority_mismatch_count = 0

    total_pred_citations = 0
    total_gold_citations = 0

    alignment = find_best_alignment(gold_claims, pred_claims)

    # claim-level evaluation aligned by semantic+citation matching
    for idx, g in enumerate(gold_claims):
        g_text = g.get('claim_text', '')
        g_text_n = normalize_text(g_text)
        g_cits = set(g.get('gold_citations', []) or [])

        p_idx = alignment.get(idx)
        p = pred_claims[p_idx] if p_idx is not None and p_idx < len(pred_claims) else {}
        p_text = p.get('claim_text', '')
        p_text_n = normalize_text(p_text)
        p_cits = set(p.get('citations', []) or [])

        overlap = len(g_cits & p_cits)
        prec = overlap / len(p_cits) if p_cits else 0.0
        rec = overlap / len(g_cits) if g_cits else 0.0
        f1 = (2 * prec * rec / (prec + rec)) if (prec + rec) > 0 else 0.0

        predicted_support = label_from_precision_recall(prec, rec)
        gold_support = g.get('support_label')

        tmatch = text_similarity(g_text, p_text)
        high_text_match = tmatch >= text_match_threshold

        if gold_support and predicted_support == gold_support:
            label_match_count += 1

        if high_text_match:
            high_text_match_count += 1

        if not p_cits:
            no_citation_count += 1
        elif overlap == 0:
            irrelevant_citation_count += 1
        elif rec < 1.0:
            insufficient_citation_count += 1

        if p_cits and not g_cits.issuperset(p_cits):
            # predicted citations include non-gold citations
            overclaim_count += 1

        # temporal mismatch proxy: gold is temporal-sensitive, text doesn't contain explicit time markers
        if g.get('temporal_sensitive'):
            has_time_marker = bool(re.search(r'(\d+\s*个?\s*工作日|\d+\s*日|期限|届满|提前|年度|月|年)', p_text_n))
            if not has_time_marker:
                temporal_mismatch_count += 1

        # exception omission proxy
        if g.get('requires_exception'):
            has_exception_marker = any(k in p_text for k in ['例外', '除外', '但', '但是', '另有规定', '从其规定'])
            if not has_exception_marker:
                exception_omission_count += 1

        # multi-authority mismatch proxy
        if g.get('requires_multi_authority'):
            # require >=2 distinct citations for such claim
            if len(p_cits) < 2:
                multi_authority_mismatch_count += 1

        details.append(
            {
                'claim_id': g.get('claim_id'),
                'matched_pred_claim_index': p_idx,
                'gold_support_label': gold_support,
                'predicted_support_label': predicted_support,
                'citation_precision': round(prec, 4),
                'citation_recall': round(rec, 4),
                'citation_f1': round(f1, 4),
                'text_match_score': round(tmatch, 4),
                'high_text_match': high_text_match,
                'gold_citations': sorted(g_cits),
                'pred_citations': sorted(p_cits),
                'flags': {
                    'irrelevant_citation': overlap == 0 and bool(p_cits),
                    'insufficient_citation': bool(p_cits) and overlap > 0 and rec < 1.0,
                    'no_citation': not bool(p_cits),
                    'overclaim': bool(p_cits) and not g_cits.issuperset(p_cits),
                    'temporal_mismatch': g.get('temporal_sensitive') and bool(re.search(r'(\\d+\\s*个?\\s*工作日|\\d+\\s*日|期限|届满|提前|年度|月|年)', p_text_n)) is False,
                    'exception_omission': g.get('requires_exception') and not any(k in p_text for k in ['例外', '除外', '但', '但是', '另有规定', '从其规定']),
                    'multi_authority_mismatch': g.get('requires_multi_authority') and len(p_cits) < 2,
                },
            }
        )

        macro_p += prec
        macro_r += rec
        macro_f1 += f1
        total_pred_citations += len(p_cits)
        total_gold_citations += len(g_cits)

    n = max(1, len(gold_claims))
    refusal = bool(pred.get('refusal', False))
    policy = gold.get('answer_policy', {})
    allow_refusal = bool(policy.get('allow_refusal', False))
    refusal_violation = refusal and not allow_refusal

    return {
        'sample_id': gold.get('sample_id'),
        'claim_count_gold': len(gold_claims),
        'claim_count_pred': len(pred_claims),
        'alignment_method': 'semantic_citation_best_match',
        'macro_citation_precision': round(macro_p / n, 4),
        'macro_citation_recall': round(macro_r / n, 4),
        'macro_citation_f1': round(macro_f1 / n, 4),
        'claim_label_accuracy': round(label_match_count / n, 4),
        'high_text_match_rate': round(high_text_match_count / n, 4),
        'irrelevant_citation_rate': round(irrelevant_citation_count / n, 4),
        'insufficient_citation_rate': round(insufficient_citation_count / n, 4),
        'no_citation_rate': round(no_citation_count / n, 4),
        'overclaim_rate': round(overclaim_count / n, 4),
        'temporal_mismatch_rate': round(temporal_mismatch_count / n, 4),
        'exception_omission_rate': round(exception_omission_count / n, 4),
        'multi_authority_mismatch_rate': round(multi_authority_mismatch_count / n, 4),
        'refusal': refusal,
        'allow_refusal': allow_refusal,
        'refusal_violation': refusal_violation,
        'total_pred_citations': total_pred_citations,
        'total_gold_citations': total_gold_citations,
        'details': details,
    }


def aggregate(results):
    if not results:
        return {
            'sample_count': 0,
            'avg_macro_citation_precision': 0.0,
            'avg_macro_citation_recall': 0.0,
            'avg_macro_citation_f1': 0.0,
            'avg_claim_label_accuracy': 0.0,
            'avg_high_text_match_rate': 0.0,
            'avg_irrelevant_citation_rate': 0.0,
            'avg_insufficient_citation_rate': 0.0,
            'avg_no_citation_rate': 0.0,
            'avg_overclaim_rate': 0.0,
            'avg_temporal_mismatch_rate': 0.0,
            'avg_exception_omission_rate': 0.0,
            'avg_multi_authority_mismatch_rate': 0.0,
            'refusal_violation_count': 0,
        }

    def avg(key):
        return round(sum(r.get(key, 0.0) for r in results) / len(results), 4)

    return {
        'sample_count': len(results),
        'avg_macro_citation_precision': avg('macro_citation_precision'),
        'avg_macro_citation_recall': avg('macro_citation_recall'),
        'avg_macro_citation_f1': avg('macro_citation_f1'),
        'avg_claim_label_accuracy': avg('claim_label_accuracy'),
        'avg_high_text_match_rate': avg('high_text_match_rate'),
        'avg_irrelevant_citation_rate': avg('irrelevant_citation_rate'),
        'avg_insufficient_citation_rate': avg('insufficient_citation_rate'),
        'avg_no_citation_rate': avg('no_citation_rate'),
        'avg_overclaim_rate': avg('overclaim_rate'),
        'avg_temporal_mismatch_rate': avg('temporal_mismatch_rate'),
        'avg_exception_omission_rate': avg('exception_omission_rate'),
        'avg_multi_authority_mismatch_rate': avg('multi_authority_mismatch_rate'),
        'refusal_violation_count': sum(1 for r in results if r.get('refusal_violation')),
    }


def main():
    parser = argparse.ArgumentParser(
        description='Evaluate model outputs against benchmark claim-level source-faithfulness metrics.'
    )
    parser.add_argument('--pred', required=True, help='Path to model output jsonl')
    parser.add_argument('--data-processed', default='data_processed', help='data_processed dir')
    parser.add_argument('--out', default='annotation/eval_report.json', help='output report json path')
    parser.add_argument('--text-match-threshold', type=float, default=0.6, help='threshold for high text match')
    args = parser.parse_args()

    pred_path = Path(args.pred)
    data_processed = Path(args.data_processed)
    out_path = Path(args.out)

    gold_by_sample = load_gold_samples(data_processed)
    pred_rows = read_jsonl(pred_path)

    results = []
    missing_gold = []

    for p in pred_rows:
        sid = p.get('sample_id')
        gold = gold_by_sample.get(sid)
        if not gold:
            missing_gold.append(sid)
            continue
        results.append(evaluate_one_sample(gold, p, args.text_match_threshold))

    summary = aggregate(results)
    report = {
        'summary': summary,
        'missing_gold_sample_ids': missing_gold,
        'results': results,
        'metric_notes': {
            'irrelevant_citation_rate': 'predicted citations exist but no overlap with gold citations',
            'insufficient_citation_rate': 'some overlap exists but recall < 1.0',
            'overclaim_rate': 'predicted citation set includes non-gold citations',
            'exception_omission_rate': 'gold requires exception but predicted claim lacks exception marker',
            'temporal_mismatch_rate': 'gold temporal-sensitive but predicted claim lacks explicit time marker',
            'multi_authority_mismatch_rate': 'gold requires multi-authority but predicted claim has <2 citations',
            'refusal_violation_count': 'prediction refused where answer_policy does not allow refusal',
        },
    }

    out_path.parent.mkdir(parents=True, exist_ok=True)
    out_path.write_text(json.dumps(report, ensure_ascii=False, indent=2), encoding='utf-8')

    print(json.dumps({'out': str(out_path).replace('\\', '/'), 'summary': summary}, ensure_ascii=False))


if __name__ == '__main__':
    main()
