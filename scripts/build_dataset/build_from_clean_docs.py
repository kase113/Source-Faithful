import csv
import json
import re
from pathlib import Path


ROOT = Path(__file__).resolve().parents[2]
if not (ROOT / 'scheme.md').exists() and (ROOT / 'lawllm' / 'scheme.md').exists():
    ROOT = ROOT / 'lawllm'

MASTER = ROOT / 'authority_master_sheet.csv'
CLEAN_DOCS = ROOT / 'data_processed' / 'rawdata_conversion' / 'clean_docs.jsonl'

OUT_DOCS = ROOT / 'data_processed' / 'authority_docs.jsonl'
OUT_ARTS = ROOT / 'data_processed' / 'authority_articles.jsonl'
OUT_CHUNKS = ROOT / 'data_processed' / 'retrieval_chunks.jsonl'
OUT_QPOOL = ROOT / 'data_processed' / 'question_pool.jsonl'


CORE12 = {
    'law_cybersecurity_2016',
    'law_data_security_2021',
    'law_pipl_2021',
    'reg_network_data_security_2025',
    'reg_ciio_security_2021',
    'rule_cybersecurity_review_2021',
    'rule_data_export_security_assessment_2022',
    'rule_pi_export_std_contract_2023',
    'rule_cross_border_data_flow_2024',
    'rule_algo_recommend_2021',
    'rule_deep_synthesis_2022',
    'rule_genai_2023',
}


ARTICLE_PAT = re.compile(r'(第[一二三四五六七八九十百千零〇两0-9]{1,10}条)')


def read_jsonl(path: Path):
    rows = []
    if not path.exists():
        return rows
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


def norm_title(s: str) -> str:
    s = (s or '').strip()
    s = s.replace('（', '(').replace('）', ')')
    s = s.replace('(公报版)', '')
    s = s.replace('《', '').replace('》', '')
    s = re.sub(r'\s+', '', s)
    return s


def split_articles(text: str):
    ms = list(ARTICLE_PAT.finditer(text or ''))
    if not ms:
        return []
    out = []
    for i, m in enumerate(ms):
        s = m.start()
        e = ms[i + 1].start() if i + 1 < len(ms) else len(text)
        out.append((i + 1, m.group(1), (text[s:e] or '').strip(), s, e))
    return out


def q_template(title: str, aid: str):
    t = title or ''
    if '个人信息' in t and ('出境' in t or '保护法' in t):
        return {
            'question': '在哪些情形下可以处理个人信息或向境外提供个人信息？',
            'question_type': '条件/要件问答',
            'domain': '数据合规',
            'authority_scope': [aid],
        }
    if '数据' in t and ('安全' in t or '跨境' in t):
        return {
            'question': '该法规对数据处理或跨境流动作出了哪些核心合规要求？',
            'question_type': '程序义务问答',
            'domain': '数据合规',
            'authority_scope': [aid],
        }
    if '网络安全' in t or '关键信息基础设施' in t:
        return {
            'question': '该法规对网络运营者或关基运营者提出了哪些义务？',
            'question_type': '直接法条问答',
            'domain': '网络安全',
            'authority_scope': [aid],
        }
    if '算法推荐' in t or '深度合成' in t or '人工智能' in t:
        return {
            'question': '该规定对平台算法或生成式人工智能服务的合规要求是什么？',
            'question_type': '程序义务问答',
            'domain': 'AI治理',
            'authority_scope': [aid],
        }
    return {
        'question': f'根据《{t}》，应重点关注哪些合规义务与法律责任？',
        'question_type': '直接法条问答',
        'domain': '数据合规',
        'authority_scope': [aid],
    }


def main():
    master_rows = list(csv.DictReader(MASTER.open('r', encoding='utf-8-sig')))
    master_by_id = {r['authority_id']: r for r in master_rows}

    title_to_id = {}
    alias_list = []
    for r in master_rows:
        for k in [r.get('title'), r.get('short_name')]:
            nk = norm_title(k)
            if nk:
                title_to_id[nk] = r['authority_id']
                alias_list.append((nk, r['authority_id']))

    docs_in = read_jsonl(CLEAN_DOCS)

    docs_out = []
    arts_out = []
    chunks_out = []
    qpool_out = []

    unmatched = []
    seen_aid = set()

    for d in docs_in:
        src_name = Path(d.get('source_file') or '').name
        src_stem = Path(src_name).stem

        candidates = [
            norm_title(d.get('title')),
            norm_title(src_stem),
        ]

        # Explicit alias for civil code source file gathered as hashed filename.
        if src_stem == 'bd53dd912c1048f2aecbaa229238334b':
            candidates.append('中华人民共和国民法典')
            candidates.append('民法典')
        aid = None
        for c in candidates:
            if c in title_to_id:
                aid = title_to_id[c]
                break
        if not aid:
            for c in candidates:
                if not c:
                    continue
                for alias, alias_id in alias_list:
                    if c in alias or alias in c:
                        aid = alias_id
                        break
                if aid:
                    break
        title_val = d.get('title') or ''
        joined = f'{title_val} {src_stem}'
        if aid == 'rule_internet_news_service_2017' and '2005' in joined:
            aid = None
        if not aid:
            unmatched.append({'source_file': src_name, 'title': d.get('title')})
            continue

        meta = master_by_id.get(aid, {})
        title = meta.get('title') or d.get('title') or src_stem
        short_name = meta.get('short_name') or title
        level = meta.get('level') or '部门规章'
        domain = meta.get('domain') or '数据合规'
        full_text = d.get('full_text') or ''

        doc_row = {
            'authority_id': aid,
            'title': title,
            'short_name': short_name,
            'level': level,
            'issuing_body': meta.get('issuing_body') or d.get('issuing_body') or '',
            'issue_date': meta.get('issue_date') or d.get('issue_date') or '',
            'effective_date': meta.get('effective_date') or d.get('effective_date') or '',
            'status': meta.get('current_status') or '现行有效',
            'source_site': meta.get('source_site') or 'rawdata',
            'source_url': meta.get('source_url') or '',
            'full_text': full_text,
            'domain_tags': [domain],
            'raw_text_path': d.get('source_file') or '',
        }
        docs_out.append(doc_row)

        arts = split_articles(full_text)
        for idx, a_no, a_text, s, e in arts:
            article_id = f'{aid}_art{idx:03d}'
            arts_out.append(
                {
                    'article_id': article_id,
                    'authority_id': aid,
                    'article_no': a_no,
                    'paragraph_no': None,
                    'item_no': None,
                    'text': a_text,
                    'char_start': s,
                    'char_end': e,
                    'topic_tags': [],
                }
            )
            chunks_out.append(
                {
                    'chunk_id': f'chunk_{aid}_{idx:03d}',
                    'authority_id': aid,
                    'article_id': article_id,
                    'chunk_type': 'article',
                    'text': a_text,
                    'citation_label': f'《{short_name}》{a_no}',
                    'level': level,
                    'effective_date': doc_row['effective_date'],
                    'domain_tags': [domain],
                }
            )

        if aid in CORE12 and aid not in seen_aid:
            t = q_template(title, aid)
            qpool_out.append(
                {
                    'sample_id': f'qpool_{aid}',
                    'domain': t['domain'],
                    'question': t['question'],
                    'question_type': t['question_type'],
                    'authority_scope': t['authority_scope'],
                    'split': 'pilot',
                }
            )
            seen_aid.add(aid)

    write_jsonl(OUT_DOCS, docs_out)
    write_jsonl(OUT_ARTS, arts_out)
    write_jsonl(OUT_CHUNKS, chunks_out)
    write_jsonl(OUT_QPOOL, qpool_out)

    print(
        json.dumps(
            {
                'docs': len(docs_out),
                'articles': len(arts_out),
                'chunks': len(chunks_out),
                'qpool': len(qpool_out),
                'unmatched_docs': len(unmatched),
                'outputs': [
                    str(OUT_DOCS.relative_to(ROOT)).replace('\\', '/'),
                    str(OUT_ARTS.relative_to(ROOT)).replace('\\', '/'),
                    str(OUT_CHUNKS.relative_to(ROOT)).replace('\\', '/'),
                    str(OUT_QPOOL.relative_to(ROOT)).replace('\\', '/'),
                ],
            },
            ensure_ascii=False,
        )
    )

    if unmatched:
        sample = unmatched[:5]
        print(json.dumps({'unmatched_sample': sample}, ensure_ascii=False))


if __name__ == '__main__':
    main()
