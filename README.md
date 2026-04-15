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
- `CONTRIBUTING.md`
- `manual_revision_examples.md`
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
- `annotation/manual_adjudication_guide.md`
- `annotation/manual_adjudication_queue.jsonl`
- `annotation/adjudication_log.jsonl`
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

### 2.5 README 精简版人工修订示例

完整长版示例见：

- [manual_revision_examples.md](./manual_revision_examples.md)

如果只想在 README 或论文正文里展示“为什么 benchmark 不能纯自动扩展”，下面这一张主表 + 3 个案例通常就够用了。

#### 主表：自动扩展到人工修订的核心变化

| 场景 | 自动扩展常见问题 | 人工修订后要求 | 代表样本 |
| --- | --- | --- | --- |
| 例外/但书题 | 只写“有例外情形”，但不拆一般规则和具体例外 | 必须分别写出一般规则、例外触发点、不能过度推出的边界 | `sample_0089` |
| 错误 citation / OCR 噪声 | 引到错误条文，或把页眉页脚、断句碎片当成 claim | 必须改成可判真的法律命题，并校正到真实支持条文 | `sample_0008`, `sample_0096` |
| 多法源联合题 | 只说“应综合判断”，但不说明每部法源各自支持什么 | 必须给出法源分工，并说明为什么单引一部法不够 | `sample_0103` |
| 程序义务题 | `reference_answer` 仍是“三个方面+省略号”模板句 | 必须改成自然语言总述，claims 继续保持逐条可核验 | `sample_0051`, `sample_0108` |

#### 案例 1：例外题必须拆开一般规则与具体例外

样本：

- [benchmark_dev.jsonl](./data_processed/benchmark_dev.jsonl)

代表 `sample_0089` 的修订逻辑：

- 自动扩展版的问题：只会写“先看一般规则，再看例外”，但没有把例外内容具体写出来。
- 人工修订版的要求：至少拆成 3 个可核验 claim。
  - 未经同意原则上不得收集、使用个人信息。
  - 即便取得同意，也不能超出提供服务所必需的范围。
  - 法律、行政法规另有规定时，从其规定，因此“同意”不是唯一依据。

这一类样本主要用来测：

- 模型是否遗漏例外
- 模型是否把一般规则绝对化
- 单一 citation 是否足以支撑“规则 + 例外”两个层面

#### 案例 2：错误 citation / OCR 碎片不能直接进入 gold

样本：

- [benchmark_train.jsonl](./data_processed/benchmark_train.jsonl)
- [benchmark_dev.jsonl](./data_processed/benchmark_dev.jsonl)

代表 `sample_0008` 与 `sample_0096` 的修订逻辑：

- `sample_0008` 原先把《个人信息保护法》的程序义务题引到了错误条文，修订后改到 `art055/art056/art061`，分别对应权利受理机制、安全治理措施、影响评估义务。
- `sample_0096` 原先继承了 `规定条件的相关材料` 这类 OCR / 断页碎片，人工修订后改成明确可核验的“电子认证服务许可申请义务”。

这一类样本主要用来测：

- citation 是否真实支持 claim
- gold 是否混入页面噪声、章节标题、说明性碎片
- 模型答错时到底是“法律理解错”，还是 benchmark 自己不干净

#### 案例 3：多法源题必须说明法源分工

样本：

- [benchmark_test.jsonl](./data_processed/benchmark_test.jsonl)

代表 `sample_0103` 的修订逻辑：

- 《在线政务服务规定》负责支持政务服务平台建设、数据共享、办事指南公开等程序义务。
- 《内容生态治理规定》负责支持平台的信息内容管理主体责任。
- 最终 gold 明确写出：只引其中一部法源，不足以得出“政务流程合规 + 内容治理合规”的完整结论。

这一类样本主要用来测：

- 检索错配
- 多法源 claim 是否被错误合并
- 模型有没有把其中一部规范“借来”支持本不该支持的结论

### 2.6 哪些内容必须人工判决

自动扩展后的样本可以作为草稿、候选标注单或训练前处理中间产物，但以下内容不能直接作为最终 gold，必须人工判决：

1. 例外/但书题中，一般规则与具体例外没有分开写清的样本。
2. 多法源题中，没有说明“哪一部法源支持哪一部分结论”的样本。
3. `gold_citations` 只是“相关”但未达到“足以支持”的样本。
4. `support_label` 处在 `supported` / `partially_supported` 边界上的样本。
5. 含有 OCR、页眉页脚、章节标题、断句碎片、错误条号映射的样本。
6. `reference_answer` 仍然是“完整回答至少应覆盖三个层面”之类模板总述的公开展示样本。

### 2.7 人工判决目录与文件形式

推荐把人工判决工作包理解成下面这个目录：

```text
annotation/
  manual_adjudication_guide.md
  manual_adjudication_queue.jsonl
  adjudication_log.jsonl
  claim_annotation_template.jsonl
data_processed/
  benchmark_train.jsonl
  benchmark_dev.jsonl
  benchmark_test.jsonl
manual_revision_examples.md
```

各文件的作用和形式如下：

| 文件 | 作用 | 形式 |
| --- | --- | --- |
| `annotation/manual_adjudication_guide.md` | 人工裁决规则说明 | Markdown |
| `annotation/manual_adjudication_queue.jsonl` | 待人工处理队列 | JSONL，每行一个待审样本 |
| `annotation/adjudication_log.jsonl` | 双人标注分歧或重大改写记录 | JSONL，每行一个 claim 级裁决记录 |
| `annotation/claim_annotation_template.jsonl` | claim 级同步模板 | JSONL，每行一个 claim |
| `data_processed/benchmark_train.jsonl` | 训练集最终版本 | JSONL，每行一个完整 benchmark 样本 |
| `data_processed/benchmark_dev.jsonl` | 开发集最终版本 | JSONL，每行一个完整 benchmark 样本 |
| `data_processed/benchmark_test.jsonl` | 测试集最终版本 | JSONL，每行一个完整 benchmark 样本 |
| `manual_revision_examples.md` | 对外展示的修订案例集 | Markdown |
| `CONTRIBUTING.md` | 人工判决与协作流程说明 | Markdown |

#### `manual_adjudication_queue.jsonl` 的建议字段

```json
{
  "sample_id": "sample_0089",
  "split": "dev",
  "question_type": "例外/但书问答",
  "authority_scope": ["rule_telecom_internet_pi_2013"],
  "review_flags": ["generic_exception_requires_manual_review"],
  "review_reason": "自动扩展仍未把一般规则和例外拆成可核验 claim"
}
```

#### `adjudication_log.jsonl` 的建议字段

```json
{
  "sample_id": "sample_0006",
  "claim_id": "sample_0006_claim_2",
  "annotator_a": "supported",
  "annotator_b": "partially_supported",
  "final_label": "partially_supported",
  "reason": "A 与 B 对支持充分性存在分歧；经裁决按更保守标准保留为 partially_supported。"
}
```

#### 人工判决后必须回写的内容

人工裁决不应只停留在 queue 或 log 中，最终必须同步回写到正式 benchmark：

1. 重写 `reference_answer`，去掉模板句和说明性废话。
2. 把 `claims` 改成可独立判真的法律命题。
3. 校正 `gold_citations` 与 `gold_minimal_spans`。
4. 必要时改 `support_label`、`requires_exception`、`requires_multi_authority`。
5. 同步更新 `annotation/claim_annotation_template.jsonl`。

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
- `avg_claim_label_accuracy`
- `avg_high_text_match_rate`
- `avg_irrelevant_citation_rate`
- `avg_insufficient_citation_rate`
- `avg_no_citation_rate`
- `avg_overclaim_rate`
- `avg_temporal_mismatch_rate`
- `avg_exception_omission_rate`
- `avg_multi_authority_mismatch_rate`
- `refusal_violation_count`

其中前三项用于 citation overlap，后续指标用于 claim-level source-faithfulness 诊断，例如区分：

- “有引用但不相关”（`irrelevant_citation_rate`）
- “有引用但不足以支持完整命题”（`insufficient_citation_rate`）
- “模型漏写例外或但书”（`exception_omission_rate`）
- “多法源题只给单法源证据”（`multi_authority_mismatch_rate`）

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
5. 运行模板化残留扫描，并保存证据文件 [annotation/gold_quality_audit.json](./annotation/gold_quality_audit.json)。
6. 检查 [annotation/adjudication_log.jsonl](./annotation/adjudication_log.jsonl) 是否覆盖多类型分歧（非单一标签翻转）。
7. 对数据来源和许可证增加明确声明。

## 7. 建议补充的仓库元信息

建议新增以下文件以提升开源可用性:

- `LICENSE`
- `CITATION.cff`
- `CONTRIBUTING.md`
- `.gitignore`

当前仓库已提供：

- [CONTRIBUTING.md](./CONTRIBUTING.md)
- [annotation/manual_adjudication_guide.md](./annotation/manual_adjudication_guide.md)
- [manual_revision_examples.md](./manual_revision_examples.md)

## 8. 当前版本说明

- 30 个 authority 主表已对齐。
- benchmark 当前规模为 120（`84/18/18`）。
- 当前公开版本已包含 `rawdata/` 原始 PDF。
- `rawdata_conversion` 属于中间层，不作为正式发布入口。
