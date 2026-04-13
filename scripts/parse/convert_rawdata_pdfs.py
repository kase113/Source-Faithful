import json
import re
from datetime import datetime, timezone
from pathlib import Path

import fitz


ROOT = Path(__file__).resolve().parents[2]
RAW_DIR = ROOT / "rawdata"
OUT_DIR = ROOT / "data_processed" / "rawdata_conversion"
MD_DIR = OUT_DIR / "md"
ART_DIR = OUT_DIR / "articles"


ARTICLE_RE = re.compile(
    r"(第[一二三四五六七八九十百千零〇两0-9]{1,10}条)"
)
DATE_RE = re.compile(r"(20\d{2}年\d{1,2}月\d{1,2}日)")


def normalize_text(text):
    text = text.replace("\r\n", "\n").replace("\r", "\n").replace("\u3000", " ")
    text = re.sub(r"[ \t]+", " ", text)
    text = re.sub(r"\n{3,}", "\n\n", text)
    return text.strip()


def extract_pdf_text(pdf_path):
    parts = []
    page_char_counts = []
    with fitz.open(pdf_path) as doc:
        for page in doc:
            txt = (page.get_text("text") or "").strip()
            parts.append(txt)
            page_char_counts.append(len(txt))
    return normalize_text("\n\n".join(parts)), page_char_counts


def guess_title(text, fallback):
    lines = [x.strip() for x in text.splitlines() if x.strip()]
    keys = (
        "法",
        "条例",
        "规定",
        "办法",
        "决定",
        "暂行",
        "试行",
    )
    for line in lines[:80]:
        if len(line) > 120:
            continue
        if any(k in line for k in keys):
            if "第" in line and "条" in line and len(line) < 20:
                continue
            return line
    return fallback


def find_issuing_body(text):
    patterns = [
        "全国人民代表大会常务委员会",
        "全国人民代表大会",
        "国务院",
        "国家互联网信息办公室",
        "中央网络安全和信息化委员会办公室",
        "公安部",
        "工业和信息化部",
    ]
    for p in patterns:
        if p in text:
            return p
    return None


def parse_dates(text):
    all_dates = list(dict.fromkeys(DATE_RE.findall(text)))
    issue_date = None
    effective_date = None

    m = re.search(
        r"(20\d{2}年\d{1,2}月\d{1,2}日)[^\n]{0,20}(公布|发布)",
        text,
    )
    if m:
        issue_date = m.group(1)

    m = re.search(r"自(20\d{2}年\d{1,2}月\d{1,2}日)起施行", text)
    if m:
        effective_date = m.group(1)
    else:
        m = re.search(r"(20\d{2}年\d{1,2}月\d{1,2}日)[^\n]{0,8}施行", text)
        if m:
            effective_date = m.group(1)

    if not issue_date and all_dates:
        issue_date = all_dates[0]
    if not effective_date and len(all_dates) > 1:
        effective_date = all_dates[1]

    return issue_date, effective_date, all_dates


def to_iso(date_zh):
    if not date_zh:
        return None
    m = re.match(r"(20\d{2})年(\d{1,2})月(\d{1,2})日", date_zh)
    if not m:
        return None
    y, mm, dd = m.groups()
    return f"{y}-{int(mm):02d}-{int(dd):02d}"


def split_articles(text):
    matches = list(ARTICLE_RE.finditer(text))
    if not matches:
        return []
    out = []
    for i, m in enumerate(matches):
        start = m.start()
        end = matches[i + 1].start() if i + 1 < len(matches) else len(text)
        out.append(
            {
                "article_index": i + 1,
                "article_no": m.group(1),
                "char_start": start,
                "char_end": end,
                "text": text[start:end].strip(),
            }
        )
    return out


def authenticity_level(text, title, issuing_body, articles, page_char_counts):
    score = 0
    reasons = []

    if len(text) >= 3000:
        score += 1
        reasons.append("full_text_length_ok")
    else:
        reasons.append("text_too_short_possible_incomplete")

    if len(articles) >= 10:
        score += 1
        reasons.append("article_structure_detected")
    elif len(articles) > 0:
        reasons.append("article_structure_detected_but_few")
    else:
        reasons.append("no_article_structure_detected")

    if any(k in title for k in ("法", "条例", "规定", "办法")):
        score += 1
        reasons.append("normative_title_pattern")

    if issuing_body:
        score += 1
        reasons.append("issuing_body_detected")
    else:
        reasons.append("issuing_body_not_detected")

    if DATE_RE.search(text):
        score += 1
        reasons.append("date_info_detected")

    sparse_pages = sum(1 for x in page_char_counts if x < 20)
    if sparse_pages >= max(2, len(page_char_counts) // 3):
        reasons.append("many_sparse_pages_possible_scan_or_extraction_issue")

    if score >= 4:
        level = "high"
    elif score >= 2:
        level = "medium"
    else:
        level = "low"

    return {"score": score, "level": level, "reasons": reasons}


def temporal_risk(title, issue_date, effective_date, text):
    reasons = []
    risk = "low"

    year = None
    for d in (effective_date, issue_date):
        if d and re.match(r"20\d{2}年", d):
            year = int(d[:4])
            break

    if "暂行" in title or "试行" in title:
        risk = "high"
        reasons.append("contains_temporary_or_trial_in_title")

    if "修订" in text[:1500]:
        reasons.append("revision_signal_detected_in_text")

    if year is not None and year <= 2020 and risk != "high":
        risk = "medium"
        reasons.append("old_publication_year_check_for_newer_version")

    if not reasons:
        reasons.append("no_obvious_outdated_signal")

    return {"risk_level": risk, "reasons": reasons}


def write_jsonl(path, rows):
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("w", encoding="utf-8") as f:
        for row in rows:
            f.write(json.dumps(row, ensure_ascii=False) + "\n")


def build_md(doc, articles):
    lines = []
    lines.append("# " + doc["title"])
    lines.append("")
    lines.append("## Metadata")
    lines.append("- source_file: " + doc["source_file"])
    lines.append("- issuing_body: " + (doc.get("issuing_body") or ""))
    lines.append("- issue_date: " + (doc.get("issue_date") or ""))
    lines.append("- effective_date: " + (doc.get("effective_date") or ""))
    lines.append("- extracted_at: " + doc["extracted_at"])
    lines.append("- article_count: " + str(doc["article_count"]))
    lines.append("")
    lines.append("## Full Text")
    lines.append("")
    lines.append(doc["full_text"])
    if articles:
        lines.append("")
        lines.append("## Article Index")
        lines.append("")
        for a in articles:
            lines.append("- " + a["article_no"])
    return "\n".join(lines).strip() + "\n"


def main():
    OUT_DIR.mkdir(parents=True, exist_ok=True)
    MD_DIR.mkdir(parents=True, exist_ok=True)
    ART_DIR.mkdir(parents=True, exist_ok=True)

    docs = []
    training = []
    report = []

    pdfs = sorted(RAW_DIR.glob("*.pdf"))
    for pdf_path in pdfs:
        text, page_char_counts = extract_pdf_text(pdf_path)
        title = guess_title(text, pdf_path.stem)
        issuing_body = find_issuing_body(text)
        issue_zh, eff_zh, all_dates = parse_dates(text)
        articles = split_articles(text)

        auth = authenticity_level(text, title, issuing_body, articles, page_char_counts)
        temp = temporal_risk(title, issue_zh, eff_zh, text)

        doc_id = "rawpdf_" + pdf_path.stem
        now = datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ")
        doc = {
            "doc_id": doc_id,
            "source_file": str(pdf_path.relative_to(ROOT)).replace("\\", "/"),
            "title": title,
            "issuing_body": issuing_body,
            "issue_date": to_iso(issue_zh),
            "effective_date": to_iso(eff_zh),
            "detected_dates": all_dates,
            "page_count": len(page_char_counts),
            "article_count": len(articles),
            "full_text": text,
            "authenticity": auth,
            "temporal_risk": temp,
            "extracted_at": now,
        }
        docs.append(doc)

        per_doc_articles = []
        for a in articles:
            article_id = f"{doc_id}_art{a['article_index']:03d}"
            row = {
                "article_id": article_id,
                "doc_id": doc_id,
                "article_no": a["article_no"],
                "char_start": a["char_start"],
                "char_end": a["char_end"],
                "text": a["text"],
            }
            per_doc_articles.append(row)
            training.append(
                {
                    "chunk_id": f"chunk_{doc_id}_{a['article_index']:03d}",
                    "doc_id": doc_id,
                    "article_id": article_id,
                    "chunk_type": "article",
                    "text": a["text"],
                    "citation_label": f"《{title}》{a['article_no']}",
                    "source_file": pdf_path.name,
                }
            )

        write_jsonl(ART_DIR / (pdf_path.stem + ".articles.jsonl"), per_doc_articles)
        (MD_DIR / (pdf_path.stem + ".md")).write_text(build_md(doc, articles), encoding="utf-8")

        report.append(
            {
                "doc_id": doc_id,
                "source_file": pdf_path.name,
                "title": title,
                "authenticity_level": auth["level"],
                "authenticity_score": auth["score"],
                "authenticity_reasons": auth["reasons"],
                "temporal_risk_level": temp["risk_level"],
                "temporal_risk_reasons": temp["reasons"],
                "issue_date": to_iso(issue_zh),
                "effective_date": to_iso(eff_zh),
                "article_count": len(articles),
                "text_length": len(text),
            }
        )

    write_jsonl(OUT_DIR / "docs.jsonl", docs)
    write_jsonl(OUT_DIR / "training_corpus.jsonl", training)
    write_jsonl(OUT_DIR / "authenticity_report.jsonl", report)

    print(
        json.dumps(
            {
                "pdf_count": len(pdfs),
                "docs_jsonl": "data_processed/rawdata_conversion/docs.jsonl",
                "training_jsonl": "data_processed/rawdata_conversion/training_corpus.jsonl",
                "report_jsonl": "data_processed/rawdata_conversion/authenticity_report.jsonl",
                "md_dir": "data_processed/rawdata_conversion/md",
                "articles_dir": "data_processed/rawdata_conversion/articles",
            },
            ensure_ascii=False,
        )
    )


if __name__ == "__main__":
    main()

