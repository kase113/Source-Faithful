import json
import random
from pathlib import Path


ROOT = Path(__file__).resolve().parents[2]

AUTH_DOCS = ROOT / 'data_processed' / 'authority_docs.jsonl'
AUTH_ARTS = ROOT / 'data_processed' / 'authority_articles.jsonl'

BENCH_TRAIN = ROOT / 'data_processed' / 'benchmark_train.jsonl'
BENCH_DEV = ROOT / 'data_processed' / 'benchmark_dev.jsonl'
BENCH_TEST = ROOT / 'data_processed' / 'benchmark_test.jsonl'

ANN_TEMPLATE = ROOT / 'annotation' / 'claim_annotation_template.jsonl'


QTYPE_COUNTS = {
    '直接法条问答': 30,
    '条件/要件问答': 24,
    '例外/但书问答': 30,
    '程序义务问答': 18,
    '多法源联合问答': 18,
}


def read_jsonl(path: Path):
    out = []
    if not path.exists():
        return out
    for line in path.read_text(encoding='utf-8').splitlines():
        line = line.strip()
        if line:
            out.append(json.loads(line))
    return out


def write_jsonl(path: Path, rows):
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open('w', encoding='utf-8') as f:
        for r in rows:
            f.write(json.dumps(r, ensure_ascii=False) + '\n')


def pick_articles(arts_by_auth, aid, n=3):
    arr = arts_by_auth.get(aid, [])
    if not arr:
        return []
    picks = []
    idxs = [0, 1, 5, 10]
    for i in idxs:
        if i < len(arr):
            picks.append(arr[i]['article_id'])
        if len(picks) >= n:
            break
    if len(picks) < n:
        for a in arr:
            aidv = a['article_id']
            if aidv not in picks:
                picks.append(aidv)
            if len(picks) >= n:
                break
    return picks[:n]


def domain_from_doc(doc):
    tags = doc.get('domain_tags') or []
    if tags:
        return tags[0]
    return '数据合规'


def q_text(qtype, title_a, title_b=None):
    if qtype == '直接法条问答':
        return f'根据《{title_a}》，回答该规范的核心义务与禁止性要求。'
    if qtype == '条件/要件问答':
        return f'在什么条件下，《{title_a}》允许或要求开展相关数据处理活动？'
    if qtype == '例外/但书问答':
        return f'《{title_a}》的一般规则有哪些例外或限制条件？'
    if qtype == '程序义务问答':
        return f'依据《{title_a}》，主体需要履行哪些关键程序性义务？'
    return f'结合《{title_a}》与《{title_b}》，该问题应如何进行多法源合规判断？'


def build_claims(sample_id, qtype, cits_primary, cits_secondary):
    c1 = cits_primary[:1]
    c2 = cits_primary[:2] if len(cits_primary) >= 2 else cits_primary[:1]
    c3 = cits_primary[1:3] if len(cits_primary) >= 3 else cits_primary[:1]

    claims = [
        {
            'claim_id': f'{sample_id}_claim_1',
            'claim_text': '该问题可由现行规范文本直接支持核心结论。',
            'claim_type': 'general_rule',
            'gold_citations': c1,
            'support_label': 'supported',
            'requires_exception': False,
            'requires_multi_authority': False,
            'temporal_sensitive': False,
            'notes': '自动生成骨架，待人工细化为具体法律主张。',
        },
        {
            'claim_id': f'{sample_id}_claim_2',
            'claim_text': '完整回答应说明适用条件、主体范围或程序要求。',
            'claim_type': 'procedural_requirement',
            'gold_citations': c2,
            'support_label': 'supported',
            'requires_exception': False,
            'requires_multi_authority': False,
            'temporal_sensitive': False,
            'notes': '用于识别条件遗漏与程序遗漏。',
        },
        {
            'claim_id': f'{sample_id}_claim_3',
            'claim_text': '如存在但书、例外或时效限制，答案应明确说明。',
            'claim_type': 'general_rule_with_exception',
            'gold_citations': c3,
            'support_label': 'partially_supported',
            'requires_exception': True,
            'requires_multi_authority': False,
            'temporal_sensitive': True,
            'notes': '用于识别 exception_omitted 与 temporal_mismatch。',
        },
    ]

    if qtype == '多法源联合问答' and cits_secondary:
        merged = []
        for x in c1 + cits_secondary[:1]:
            if x and x not in merged:
                merged.append(x)
        claims[1]['claim_text'] = '该结论需要联合两个法源才能完整成立。'
        claims[1]['claim_type'] = 'cross_border_requirement'
        claims[1]['gold_citations'] = merged
        claims[1]['requires_multi_authority'] = True

    if qtype == '例外/但书问答':
        claims[0]['claim_type'] = 'general_rule_with_exception'
        claims[0]['requires_exception'] = True

    if qtype == '条件/要件问答':
        claims[0]['claim_type'] = 'scope_of_application'

    return claims


def main():
    docs = read_jsonl(AUTH_DOCS)
    arts = read_jsonl(AUTH_ARTS)

    docs = sorted(docs, key=lambda x: x['authority_id'])
    if len(docs) < 30:
        raise RuntimeError(f'authority_docs too small: {len(docs)}')

    arts_by_auth = {}
    for a in arts:
        aid = a.get('authority_id')
        if aid:
            arts_by_auth.setdefault(aid, []).append(a)
    for aid in arts_by_auth:
        arts_by_auth[aid].sort(key=lambda x: x.get('article_id', ''))

    qtypes = []
    for k, v in QTYPE_COUNTS.items():
        qtypes.extend([k] * v)
    random.seed(20260412)
    random.shuffle(qtypes)

    total = len(qtypes)
    samples = []
    for i in range(total):
        doc_a = docs[i % len(docs)]
        doc_b = docs[(i + 7) % len(docs)]

        aid_a = doc_a['authority_id']
        aid_b = doc_b['authority_id']

        qtype = qtypes[i]
        sid = f'sample_{i+1:04d}'

        cits_a = pick_articles(arts_by_auth, aid_a, n=3)
        cits_b = pick_articles(arts_by_auth, aid_b, n=1)

        if qtype == '多法源联合问答':
            authority_scope = [aid_a, aid_b]
            gold_auth = []
            for x in cits_a[:2] + cits_b[:1]:
                if x and x not in gold_auth:
                    gold_auth.append(x)
            q = q_text(qtype, doc_a['short_name'], doc_b['short_name'])
        else:
            authority_scope = [aid_a]
            gold_auth = cits_a
            q = q_text(qtype, doc_a['short_name'])

        claims = build_claims(sid, qtype, cits_a, cits_b)

        sample = {
            'sample_id': sid,
            'domain': domain_from_doc(doc_a),
            'question': q,
            'question_type': qtype,
            'authority_scope': authority_scope,
            'gold_authorities': gold_auth,
            'gold_minimal_spans': gold_auth[:2],
            'reference_answer': '自动扩展样本：请人工改写为可发表版本的参考答案。',
            'claims': claims,
            'answer_policy': {
                'allow_refusal': False,
                'must_mention_exception': True,
                'must_mention_temporal_validity': True,
            },
            'split': 'train',
        }
        samples.append(sample)

    # split 70/15/15 -> 84/18/18 for 120
    train_n, dev_n = 84, 18
    train = samples[:train_n]
    dev = samples[train_n:train_n + dev_n]
    test = samples[train_n + dev_n:]

    for x in train:
        x['split'] = 'train'
    for x in dev:
        x['split'] = 'dev'
    for x in test:
        x['split'] = 'test'

    write_jsonl(BENCH_TRAIN, train)
    write_jsonl(BENCH_DEV, dev)
    write_jsonl(BENCH_TEST, test)

    template = []
    for s in train + dev + test:
        for c in s['claims']:
            template.append(
                {
                    'sample_id': s['sample_id'],
                    'split': s['split'],
                    'question': s['question'],
                    'claim_id': c['claim_id'],
                    'claim_text': c['claim_text'],
                    'claim_type': c['claim_type'],
                    'gold_citations': c['gold_citations'],
                    'support_label': c['support_label'],
                    'requires_exception': c['requires_exception'],
                    'requires_multi_authority': c['requires_multi_authority'],
                    'temporal_sensitive': c['temporal_sensitive'],
                    'annotator_a': '',
                    'annotator_b': '',
                    'final_label': '',
                    'notes': c['notes'],
                }
            )

    write_jsonl(ANN_TEMPLATE, template)

    dist = {}
    for s in samples:
        dist[s['question_type']] = dist.get(s['question_type'], 0) + 1

    print(
        json.dumps(
            {
                'total_samples': len(samples),
                'split': {'train': len(train), 'dev': len(dev), 'test': len(test)},
                'question_type_distribution': dist,
                'annotation_rows': len(template),
                'outputs': [
                    str(BENCH_TRAIN.relative_to(ROOT)).replace('\\', '/'),
                    str(BENCH_DEV.relative_to(ROOT)).replace('\\', '/'),
                    str(BENCH_TEST.relative_to(ROOT)).replace('\\', '/'),
                    str(ANN_TEMPLATE.relative_to(ROOT)).replace('\\', '/'),
                ],
            },
            ensure_ascii=False,
        )
    )


if __name__ == '__main__':
    main()

