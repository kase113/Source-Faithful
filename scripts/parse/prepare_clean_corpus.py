import json
from pathlib import Path


ROOT = Path(__file__).resolve().parents[2]
if not (ROOT / 'scheme.md').exists() and (ROOT / 'lawllm' / 'scheme.md').exists():
    ROOT = ROOT / 'lawllm'

CONV_DIR = ROOT / 'data_processed' / 'rawdata_conversion'
DOCS_IN = CONV_DIR / 'docs.jsonl'
TRAIN_IN = CONV_DIR / 'training_corpus.jsonl'

DOCS_OUT = CONV_DIR / 'clean_docs.jsonl'
TRAIN_OUT = CONV_DIR / 'clean_training_corpus.jsonl'
FILTER_LOG = CONV_DIR / 'clean_filter_log.jsonl'

EXCLUDE_TOKENS = [
    '\u4e2d\u56fd\u6cd5\u4ee4\u30a2\u30c3\u30d7\u30c7\u30fc\u30c8\uff08\u7b97\u6cd5\u63a8\u8350\u7ba1\u7406\u89c4\u5b9a\uff09',
    '\u56fd\u5bb6\u4e92\u8054\u7f51\u4fe1\u606f\u529e\u516c\u5ba4\u516c\u5e03\u300a\u7f51\u4fe1\u90e8\u95e8\u884c\u653f\u6267\u6cd5\u7a0b\u5e8f\u89c4\u5b9a\u300b',
]


def read_jsonl(path: Path):
    if not path.exists():
        return []
    rows = []
    for line in path.read_text(encoding='utf-8').splitlines():
        line = line.strip()
        if not line:
            continue
        rows.append(json.loads(line))
    return rows


def write_jsonl(path: Path, rows):
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open('w', encoding='utf-8') as f:
        for row in rows:
            f.write(json.dumps(row, ensure_ascii=False) + '\n')


def exclusion_reason(row):
    title = (row.get('title') or '').strip()
    source_file = (row.get('source_file') or '').strip()
    haystack = f'{source_file} {title}'

    for token in EXCLUDE_TOKENS:
        if token in haystack:
            if '\u30a2\u30c3\u30d7\u30c7\u30fc\u30c8' in token:
                return 'digest_or_secondary_summary'
            return 'news_release_not_full_regulation_text'

    return None


def main():
    docs = read_jsonl(DOCS_IN)
    train = read_jsonl(TRAIN_IN)

    kept_docs = []
    dropped = []
    kept_ids = set()

    for d in docs:
        doc_id = d.get('doc_id')
        merged = {
            'title': d.get('title'),
            'source_file': Path(d.get('source_file') or '').name,
        }

        reason = exclusion_reason(merged)
        if reason:
            dropped.append(
                {
                    'doc_id': doc_id,
                    'source_file': merged['source_file'],
                    'title': merged['title'],
                    'exclude_reason': reason,
                }
            )
            continue

        kept_docs.append(d)
        kept_ids.add(doc_id)

    kept_train = [t for t in train if t.get('doc_id') in kept_ids]

    write_jsonl(DOCS_OUT, kept_docs)
    write_jsonl(TRAIN_OUT, kept_train)
    write_jsonl(FILTER_LOG, dropped)

    print(
        json.dumps(
            {
                'input_docs': len(docs),
                'kept_docs': len(kept_docs),
                'dropped_docs': len(dropped),
                'input_chunks': len(train),
                'kept_chunks': len(kept_train),
                'clean_docs': str(DOCS_OUT.relative_to(ROOT)).replace('\\', '/'),
                'clean_training': str(TRAIN_OUT.relative_to(ROOT)).replace('\\', '/'),
                'filter_log': str(FILTER_LOG.relative_to(ROOT)).replace('\\', '/'),
            },
            ensure_ascii=False,
        )
    )


if __name__ == '__main__':
    main()
