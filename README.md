# LawLLM: 中文法律 RAG Benchmark（30 法源）

本项目用于构建并评测中文法律场景下的 RAG（Retrieval-Augmented Generation）能力，重点关注:

- 引用是否真实存在
- 引用是否相关
- 引用是否足以支持 claim
- 是否遗漏例外条款
- 是否存在规范误适用和检索错配

当前版本按公开发布要求，包含“必须开源内容 + rawdata 原始 PDF 数据”。

## 1. 本仓库实际开源范围

本仓库已按以下范围发布:

### 1.1 必须开源内容（复现最小闭环）

- `README.md`（本文件）
- `authority_master_sheet.csv`
- `scheme.md`
- `data_processed/authority_docs.jsonl`
- `data_processed/authority_articles.jsonl`
- `data_processed/retrieval_chunks.jsonl`
- `data_processed/benchmark_train.jsonl`
- `data_processed/benchmark_dev.jsonl`
- `data_processed/benchmark_test.jsonl`
- `annotation/guidelines_v1.md`
- `annotation/schema_v1.json`
- `annotation/claim_annotation_template.jsonl`
- `scripts/parse/convert_rawdata_pdfs.py`
- `scripts/parse/prepare_clean_corpus.py`
- `scripts/build_dataset/build_from_clean_docs.py`
- `scripts/build_dataset/expand_benchmark_pilot.py`
- `scripts/eval/eval_model_outputs.py`

### 1.2 本次额外开源内容

- `rawdata/`（原始 PDF 数据，31 个文件）

### 1.3 本仓库未纳入的内容

以下内容不在本次公开范围内（用于减少噪声和中间产物体积）:

- `data_raw/`
- `data_processed/rawdata_conversion/`
- 临时模型输出与 mock 结果（除正式示例外）

## 2. 数据集规范

### 2.1 数据层级

建议统一按 4 层理解:

1. 原始层: `rawdata/`, `data_raw/`
2. 转换层: `data_processed/rawdata_conversion/`
3. 正式语料层: `authority_docs`, `authority_articles`, `retrieval_chunks`
4. Benchmark 与标注层: `benchmark_*`, `annotation/*`

对外发布和实验复现应默认使用第 3、4 层，原始层用于追溯与重处理。

### 2.2 关键文件说明

- `authority_master_sheet.csv`: 30 个法源主表台账，authority_id 是全项目主键。
- `authority_docs.jsonl`: 文档级规范文本。
- `authority_articles.jsonl`: 条款级结构化文本。
- `retrieval_chunks.jsonl`: 检索单元，评测引用时的核心基准。
- `benchmark_train/dev/test.jsonl`: 问题、reference answer、claim 与 gold citation。
- `annotation/schema_v1.json`: 标注 schema。
- `annotation/guidelines_v1.md`: 标注流程与标准。

### 2.3 样本结构（benchmark）

每条 benchmark 样本建议至少包含以下字段:

- `sample_id`
- `question`
- `question_type`
- `authority_scope`
- `reference_answer`
- `claims[]`
- `claims[].claim_id`
- `claims[].claim_text`
- `claims[].gold_citations`
- `claims[].support_label`

### 2.4 标注标签约定

`support_label` 使用如下枚举:

- `supported`
- `partially_supported`
- `unsupported`
- `conflicting`
- `insufficient_information`

## 3. 实验规范

### 3.1 统一评测目标

模型必须回答同一批 `benchmark_test.jsonl` 样本，且输出统一 JSON 结构，才能做公平对比。

### 3.2 模型输出格式

每条输出建议为一行 JSON（JSONL），最低字段要求:

```json
{
  "sample_id": "sample_0001",
  "final_answer": "...",
  "claims": [
    {
      "claim_text": "...",
      "citations": ["law_pipl_2021_art013"],
      "confidence": 0.82
    }
  ],
  "refusal": false,
  "refusal_reason": ""
}
```

说明:

- `citations` 必须引用 `authority_articles.jsonl` 中真实 `article_id`。
- 建议每题 `claims` 数量为 2-4。
- 证据不足时允许拒答（`refusal=true`）。

### 3.3 主要指标

`scripts/eval/eval_model_outputs.py` 当前输出:

- `avg_macro_citation_precision`
- `avg_macro_citation_recall`
- `avg_macro_citation_f1`

## 4. 复现实验流程（端到端）

以下命令默认在仓库根目录执行。

### 4.1 环境准备

```bash
python -m venv .venv
. .venv/Scripts/activate
pip install pymupdf
```

说明: 当前脚本除 `PyMuPDF` 外主要使用 Python 标准库。

### 4.2 从原始 PDF 转换中间语料（可选）

如果你只复现实验，不需要这一步。若要从原始 PDF 重建流水线，执行:

```bash
python scripts/parse/convert_rawdata_pdfs.py
python scripts/parse/prepare_clean_corpus.py
python scripts/build_dataset/build_from_clean_docs.py
```

### 4.3 生成 benchmark（如需重建）

```bash
python scripts/build_dataset/expand_benchmark_pilot.py
```

默认生成:

- `data_processed/benchmark_train.jsonl`
- `data_processed/benchmark_dev.jsonl`
- `data_processed/benchmark_test.jsonl`
- `annotation/claim_annotation_template.jsonl`

### 4.4 运行模型并保存输出

将模型预测保存为:

- `annotation/<model_name>_outputs.jsonl`

### 4.5 评测模型输出

```bash
python scripts/eval/eval_model_outputs.py --pred annotation/<model_name>_outputs.jsonl --data-processed data_processed --out annotation/<model_name>_eval_report.json
```

## 5. 网页会话实操（来自教程第 13 节）

下面用真实样本 `sample_0103` 做一遍“从网页会话到评测”的完整演示。

### 5.1 选样本（真实）

来自 `data_processed/benchmark_test.jsonl`：

- `sample_id`: `sample_0103`
- `question`: `结合《在线政务服务规定》与《内容生态治理规定》，该问题应如何进行多法源合规判断？`
- `authority_scope`: `["reg_online_gov_services_2019","rule_content_ecology_2019"]`

### 5.2 组候选法条（示例取 6 条）

从 `data_processed/retrieval_chunks.jsonl` 里按 `authority_scope` 过滤后，放入以下条款（示例）：

1. `reg_online_gov_services_2019_art001`：《在线政务服务规定》第一条（立法目的、政务服务规范化）
2. `reg_online_gov_services_2019_art002`：《在线政务服务规定》第二条（全国一体化平台、跨地区跨部门数据共享）
3. `reg_online_gov_services_2019_art006`：《在线政务服务规定》第六条（办事指南、受理条件、流程公开）
4. `rule_content_ecology_2019_art001`：《内容生态治理规定》第一条（立法目的与依据）
5. `rule_content_ecology_2019_art002`：《内容生态治理规定》第二条（适用范围与治理定义）
6. `rule_content_ecology_2019_art008`：《内容生态治理规定》第八条（平台主体责任）

### 5.3 网页会话实际发送内容（可直接复制）

在网页端（如 ChatGPT）新建会话。

System（如平台不支持 system，就把这段放在用户消息最前面）：

```text
你是中文法律合规助手。你必须仅基于给定候选法条作答。
不得编造法条或引用；证据不足时允许拒答。
只输出 JSON，不输出任何解释性文本。
```

User：

```text
请处理以下法律问答样本。

sample_id: sample_0103
question: 结合《在线政务服务规定》与《内容生态治理规定》，该问题应如何进行多法源合规判断？
authority_scope: ["reg_online_gov_services_2019","rule_content_ecology_2019"]

候选法条（你只能引用下面出现的 article_id）：
- reg_online_gov_services_2019_art001: 第一条 为了全面提升政务服务规范化、便利化水平，为企业和群众提供高效便捷政务服务，优化营商环境，制定本规定。
- reg_online_gov_services_2019_art002: 第二条 国家加快建设全国一体化在线政务服务平台，推动政务服务事项全国标准统一、全流程网上办理，促进跨地区跨部门跨层级数据共享和业务协同。
- reg_online_gov_services_2019_art006: 第六条 政务服务机构应按规范化、标准化要求编制办事指南，明确受理条件、材料、流程等，并在平台公布。
- rule_content_ecology_2019_art001: 第一条 为营造良好网络生态、保障合法权益、维护国家安全和公共利益，制定本规定。
- rule_content_ecology_2019_art002: 第二条 中华人民共和国境内网络信息内容生态治理活动适用本规定。
- rule_content_ecology_2019_art008: 第八条 网络信息内容服务平台应履行信息内容管理主体责任，加强平台生态治理。

请严格输出以下 JSON 结构：
{
  "sample_id": "sample_0103",
  "final_answer": "......",
  "claims": [
    {
      "claim_text": "......",
      "citations": ["article_id_1", "article_id_2"],
      "confidence": 0.0
    }
  ],
  "refusal": false,
  "refusal_reason": ""
}

约束：
1) citations 只能填写候选法条中的 article_id。
2) claims 数量为 2-4。
3) 证据不足时，refusal=true，并说明 refusal_reason。
```

### 5.4 一次“合格输出”参考（示例）

模型返回内容只要满足结构和约束即可，不要求和下面逐字一致：

```json
{
  "sample_id": "sample_0103",
  "final_answer": "该问题应采用多法源联合判断：先依据《在线政务服务规定》确认政务服务平台建设、数据共享及办事流程公开等程序义务，再依据《内容生态治理规定》确认网络信息内容治理的适用范围与平台主体责任，形成“政务服务流程合规+内容生态治理合规”的组合结论；同时应提示法律法规另有规定或特殊情形下的边界。",
  "claims": [
    {
      "claim_text": "进行该问题判断需要联合《在线政务服务规定》与《内容生态治理规定》两个法源。",
      "citations": [
        "reg_online_gov_services_2019_art001",
        "rule_content_ecology_2019_art001"
      ],
      "confidence": 0.86
    },
    {
      "claim_text": "政务服务侧应覆盖一体化平台建设、跨地区跨部门数据共享以及办事指南公开等程序要求。",
      "citations": [
        "reg_online_gov_services_2019_art002",
        "reg_online_gov_services_2019_art006"
      ],
      "confidence": 0.84
    },
    {
      "claim_text": "内容生态侧需确认适用范围并强调平台承担信息内容管理主体责任。",
      "citations": [
        "rule_content_ecology_2019_art002",
        "rule_content_ecology_2019_art008"
      ],
      "confidence": 0.82
    }
  ],
  "refusal": false,
  "refusal_reason": ""
}
```

### 5.5 落盘为 JSONL（手工）

把上面的 JSON 压成一行，追加到：

- `annotation/gpt-5_outputs.jsonl`

建议每完成 1 条就保存一次，避免会话丢失。

### 5.6 质量自检（建议每 3 条做一次）

1. JSON 是否可解析（不能有注释、不能丢引号）
2. `sample_id` 是否正确
3. `citations` 是否全部来自候选条款
4. `claims` 数量是否在 2-4
5. 是否按证据情况正确设置 `refusal`

可用命令快速检查 JSONL 是否损坏：

```powershell
Get-Content annotation/gpt-5_outputs.jsonl -Encoding UTF8 | ForEach-Object { $_ | ConvertFrom-Json | Out-Null }
```

没有报错即表示每行都是合法 JSON。

### 5.7 跑评测（该模型跑完 18 条后）

```bash
python scripts/eval/eval_model_outputs.py --pred annotation/gpt-5_outputs.jsonl --data-processed data_processed --out annotation/gpt-5_eval_report.json
```

到这里，一次完整网页会话实验就闭环完成了。后续你只需要替换 `sample_id/question/authority_scope/candidate_chunks`，按同样模板跑剩余样本。

## 6. 发布前检查清单

开源前建议至少完成以下检查:

1. 所有公开数据文件均为 UTF-8 编码。
2. `benchmark_*` 与 `annotation` 字段命名一致。
3. 删除或脱敏本地绝对路径、个人信息、内部备注。
4. 检查 `rawdata/` 与 `data_raw/` 是否误提交。
5. 对数据来源和许可证增加明确声明。

## 7. 建议补充的仓库元信息

建议新增以下文件以提升开源可用性:

- `LICENSE`
- `CITATION.cff`
- `CONTRIBUTING.md`
- `.gitignore`

## 8. 当前版本说明

- 30 个 authority 主表已对齐。
- benchmark 当前规模为 120（`84/18/18`）。
- 当前公开版本已包含 `rawdata/` 原始 PDF。
- `rawdata_conversion` 属于中间层，不作为正式发布入口。
