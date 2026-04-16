import argparse
import json
import re
import subprocess
import sys
from pathlib import Path


def read_jsonl(path: Path):
    rows = []
    for line in path.read_text(encoding='utf-8').splitlines():
        line = line.strip()
        if line:
            rows.append(json.loads(line))
    return rows


def write_jsonl(path: Path, rows):
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open('w', encoding='utf-8', newline='\n') as f:
        for r in rows:
            f.write(json.dumps(r, ensure_ascii=False) + '\n')


def mutate_article_id(article_id: str) -> str:
    m = re.search(r'^(.*_art)(\d+)$', article_id or '')
    if not m:
        return article_id
    prefix, num = m.group(1), m.group(2)
    return f'{prefix}{int(num) + 1:0{len(num)}d}'


def dedup_keep_order(items):
    out = []
    seen = set()
    for x in items:
        if x and x not in seen:
            seen.add(x)
            out.append(x)
    return out


def build_claim_output(gold_claim: dict, mode: str, sample_gold_authorities: list[str], idx: int):
    gold_text = gold_claim.get('claim_text', '')
    gold_cits = gold_claim.get('gold_citations', []) or []
    first_gold = gold_cits[0] if gold_cits else (sample_gold_authorities[0] if sample_gold_authorities else '')
    noise_cit = mutate_article_id(first_gold) if first_gold else ''

    if mode == 'weak':
        return {
            'claim_text': 'The conclusion can be inferred from current rules.',
            'citations': [noise_cit] if noise_cit else [],
            'confidence': 0.58,
        }

    if mode == 'balanced':
        cits = gold_cits[:1] if gold_cits else []
        if idx % 2 == 0 and noise_cit:
            cits = dedup_keep_order(cits + [noise_cit])
        return {
            'claim_text': gold_text,
            'citations': cits,
            'confidence': 0.74,
        }

    # strong baseline: near-upper-bound deterministic reference-style output.
    return {
        'claim_text': gold_text,
        'citations': gold_cits,
        'confidence': 0.9,
    }


def build_outputs(gold_rows: list[dict], mode: str):
    outputs = []
    for row in gold_rows:
        sample_id = row.get('sample_id')
        gold_claims = row.get('claims', []) or []
        gold_authorities = row.get('gold_authorities', []) or []

        pred_claims = []
        for idx, c in enumerate(gold_claims):
            pred_claims.append(build_claim_output(c, mode, gold_authorities, idx))

        if mode == 'weak':
            final_answer = 'Insufficiently grounded summary from broad legal context.'
        elif mode == 'balanced':
            final_answer = 'Partially grounded answer with selective citations.'
        else:
            final_answer = row.get('reference_answer', '')

        outputs.append(
            {
                'sample_id': sample_id,
                'final_answer': final_answer,
                'claims': pred_claims,
                'refusal': False,
                'refusal_reason': '',
            }
        )
    return outputs


def run_eval(python_exe: str, pred_path: Path, data_processed: Path, report_path: Path):
    cmd = [
        python_exe,
        str(Path('scripts/eval/eval_model_outputs.py')),
        '--pred',
        str(pred_path),
        '--data-processed',
        str(data_processed),
        '--out',
        str(report_path),
    ]
    subprocess.run(cmd, check=True)
    return json.loads(report_path.read_text(encoding='utf-8'))


def write_summary_md(path: Path, summary_rows: list[dict]):
    lines = [
        '# Baseline Eval Summary',
        '',
        '| baseline | sample_count | citation_f1 | label_acc | overclaim_rate | exception_omission_rate |',
        '|---|---:|---:|---:|---:|---:|',
    ]
    for r in summary_rows:
        lines.append(
            '| {baseline} | {sample_count} | {citation_f1:.4f} | {label_acc:.4f} | {overclaim:.4f} | {exception_omit:.4f} |'.format(
                baseline=r['baseline'],
                sample_count=r['sample_count'],
                citation_f1=r['avg_macro_citation_f1'],
                label_acc=r['avg_claim_label_accuracy'],
                overclaim=r['avg_overclaim_rate'],
                exception_omit=r['avg_exception_omission_rate'],
            )
        )
    path.write_text('\n'.join(lines) + '\n', encoding='utf-8')


def main():
    parser = argparse.ArgumentParser(description='Generate weak/balanced/strong baseline outputs and optional eval reports.')
    parser.add_argument('--data-processed', default='data_processed', help='Path to data_processed directory')
    parser.add_argument('--out-dir', default='annotation', help='Directory to write outputs/reports')
    parser.add_argument('--split-file', default='benchmark_test.jsonl', help='Benchmark file name under data_processed')
    parser.add_argument('--run-eval', action='store_true', help='Run evaluator and produce baseline summary')
    parser.add_argument('--python', default=sys.executable, help='Python executable used to run evaluator')
    args = parser.parse_args()

    data_processed = Path(args.data_processed)
    out_dir = Path(args.out_dir)
    split_path = data_processed / args.split_file
    gold_rows = read_jsonl(split_path)

    modes = ['weak', 'balanced', 'strong']
    generated = []
    summary_rows = []

    for mode in modes:
        outputs = build_outputs(gold_rows, mode=mode)
        out_path = out_dir / f'baseline_{mode}_outputs.jsonl'
        write_jsonl(out_path, outputs)
        generated.append(str(out_path).replace('\\', '/'))

        if args.run_eval:
            report_path = out_dir / f'baseline_{mode}_eval_report.json'
            report = run_eval(args.python, out_path, data_processed, report_path)
            generated.append(str(report_path).replace('\\', '/'))
            s = report.get('summary', {})
            summary_rows.append(
                {
                    'baseline': mode,
                    'sample_count': s.get('sample_count', 0),
                    'avg_macro_citation_f1': s.get('avg_macro_citation_f1', 0.0),
                    'avg_claim_label_accuracy': s.get('avg_claim_label_accuracy', 0.0),
                    'avg_overclaim_rate': s.get('avg_overclaim_rate', 0.0),
                    'avg_exception_omission_rate': s.get('avg_exception_omission_rate', 0.0),
                }
            )

    summary_json_path = out_dir / 'baseline_eval_summary.json'
    summary_md_path = out_dir / 'baseline_eval_summary.md'

    if args.run_eval:
        summary_json = {
            'split_file': args.split_file,
            'baselines': summary_rows,
        }
        summary_json_path.write_text(json.dumps(summary_json, ensure_ascii=False, indent=2), encoding='utf-8')
        write_summary_md(summary_md_path, summary_rows)
        generated.extend(
            [
                str(summary_json_path).replace('\\', '/'),
                str(summary_md_path).replace('\\', '/'),
            ]
        )

    print(json.dumps({'generated_files': generated}, ensure_ascii=False))


if __name__ == '__main__':
    main()
