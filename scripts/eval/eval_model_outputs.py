import argparse
import json
import re
from pathlib import Path


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


def load_gold_samples(data_processed: Path):
    files = [
        data_processed / 'benchmark_train.jsonl',
        data_processed / 'benchmark_dev.jsonl',
        data_processed / 'benchmark_test.jsonl',
    ]
    all_rows = []
    for f in files:
        all_rows.extend(read_jsonl(f))

    by_sample = {r.get('sample_id'): r for r in all_rows if r.get('sample_id')}
    return by_sample


def label_from_precision_recall(prec: float, rec: float) -> str:
    if rec == 0.0:
        return 'unsupported'
    if prec == 1.0 and rec == 1.0:
        return 'supported'
    return 'partially_supported'


def evaluate_one_sample(gold: dict, pred: dict):
    gold_claims = gold.get('claims', [])
    pred_claims = pred.get('claims', [])

    details = []
    macro_p = 0.0
    macro_r = 0.0
    macro_f1 = 0.0

    for idx, g in enumerate(gold_claims):
        g_text = normalize_text(g.get('claim_text', ''))
        g_cits = set(g.get('gold_citations', []) or [])

        p = pred_claims[idx] if idx < len(pred_claims) else {}
        p_text = normalize_text(p.get('claim_text', ''))
        p_cits = set(p.get('citations', []) or [])

        overlap = len(g_cits & p_cits)
        prec = overlap / len(p_cits) if p_cits else 0.0
        rec = overlap / len(g_cits) if g_cits else 0.0
        f1 = (2 * prec * rec / (prec + rec)) if (prec + rec) > 0 else 0.0

        # text similarity: simple containment proxy
        text_match = 0.0
        if g_text and p_text:
            if g_text in p_text or p_text in g_text:
                text_match = 1.0
            else:
                # character overlap ratio
                gs = set(g_text)
                ps = set(p_text)
                text_match = len(gs & ps) / max(1, len(gs | ps))

        predicted_support = label_from_precision_recall(prec, rec)

        details.append(
            {
                'claim_id': g.get('claim_id'),
                'gold_support_label': g.get('support_label'),
                'predicted_support_label': predicted_support,
                'citation_precision': round(prec, 4),
                'citation_recall': round(rec, 4),
                'citation_f1': round(f1, 4),
                'text_match_score': round(text_match, 4),
                'gold_citations': sorted(g_cits),
                'pred_citations': sorted(p_cits),
            }
        )

        macro_p += prec
        macro_r += rec
        macro_f1 += f1

    n = max(1, len(gold_claims))
    return {
        'sample_id': gold.get('sample_id'),
        'claim_count_gold': len(gold_claims),
        'claim_count_pred': len(pred_claims),
        'macro_citation_precision': round(macro_p / n, 4),
        'macro_citation_recall': round(macro_r / n, 4),
        'macro_citation_f1': round(macro_f1 / n, 4),
        'details': details,
    }


def aggregate(results):
    if not results:
        return {
            'sample_count': 0,
            'avg_macro_citation_precision': 0.0,
            'avg_macro_citation_recall': 0.0,
            'avg_macro_citation_f1': 0.0,
        }

    p = sum(r['macro_citation_precision'] for r in results) / len(results)
    r = sum(r['macro_citation_recall'] for r in results) / len(results)
    f1 = sum(r['macro_citation_f1'] for r in results) / len(results)
    return {
        'sample_count': len(results),
        'avg_macro_citation_precision': round(p, 4),
        'avg_macro_citation_recall': round(r, 4),
        'avg_macro_citation_f1': round(f1, 4),
    }


def main():
    parser = argparse.ArgumentParser(
        description='Evaluate model outputs against benchmark claim-level citations.'
    )
    parser.add_argument('--pred', required=True, help='Path to model output jsonl')
    parser.add_argument('--data-processed', default='data_processed', help='data_processed dir')
    parser.add_argument('--out', default='annotation/eval_report.json', help='output report json path')
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
        results.append(evaluate_one_sample(gold, p))

    summary = aggregate(results)
    report = {
        'summary': summary,
        'missing_gold_sample_ids': missing_gold,
        'results': results,
    }

    out_path.parent.mkdir(parents=True, exist_ok=True)
    out_path.write_text(json.dumps(report, ensure_ascii=False, indent=2), encoding='utf-8')

    print(json.dumps({'out': str(out_path).replace('\\', '/'), 'summary': summary}, ensure_ascii=False))


if __name__ == '__main__':
    main()

