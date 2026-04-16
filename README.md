# Source-Faithful 数据集仓库

本仓库现在只保留“数据集发布”相关内容：

- 法源原始 PDF（`rawdata/`）
- 结构化条文与 benchmark（`data_processed/`）
- 标注规范与人工裁决记录（`annotation/`）
- 最小说明文件（本 README、`scheme.md`、`authority_master_sheet.csv`）

说明：训练/构建脚本与模型评测脚本已从本仓库移除，避免仓库用途混杂。

## 仓库结构

- `rawdata/`: 原始法规 PDF
- `data_processed/`: 结构化数据与 train/dev/test
- `annotation/`: 标注规范、模板、裁决日志与质量审计
- `authority_master_sheet.csv`: 30 个法源主表
- `scheme.md`: 字段与设计说明

## `data_processed/` 文件含义（不含 `rawdata_conversion/`）

| 文件 | 含义 | 典型用途 |
|---|---|---|
| `authority_docs.jsonl` | 法源级文档记录（每部规范一条或多条文档元记录） | 查看法源范围、来源信息 |
| `authority_articles.jsonl` | 条款级结构化文本（`article_id` 主键） | citation 对齐、证据核验 |
| `retrieval_chunks.jsonl` | 检索片段库（检索阶段候选证据） | RAG 检索输入 |
| `question_pool.jsonl` | 问题池（候选问法） | 构建/扩展 benchmark |
| `benchmark_train.jsonl` | 训练集（含 claim 与 gold citations） | 训练与误差分析 |
| `benchmark_dev.jsonl` | 开发集 | 调参/模型选择 |
| `benchmark_test.jsonl` | 测试集（最终评测） | 固定对比与论文主结果 |

## 标签与字段速读

每条 benchmark 样本核心字段：

- `sample_id`, `question`, `question_type`, `authority_scope`
- `gold_authorities`, `gold_minimal_spans`
- `reference_answer`
- `claims[]`（claim 级真值）
- `answer_policy`
- `split`

`claims[]` 关键标签：

- `claim_type`: 主张类型（如 `general_rule` / `specific_exception` / `procedural_requirement`）
- `support_label`: 支持关系（`supported` / `partially_supported` / `unsupported` / `conflicting` / `insufficient_information`）
- `gold_citations`: 支撑该 claim 的条文 `article_id`
- `requires_exception`, `requires_multi_authority`, `temporal_sensitive`: 题目判分时的附加要求

## 示例与分析记录（sample_0001）

下面是 `benchmark_train.jsonl` 的 `sample_0001`（原样示例）：

```json
{
  "sample_id": "sample_0001",
  "domain": "网络安全",
  "question": "《反电信网络诈骗法》的一般规则有哪些例外或限制条件？",
  "question_type": "例外/但书问答",
  "authority_scope": ["law_anti_telecom_fraud_2022"],
  "gold_authorities": ["law_anti_telecom_fraud_2022_art012", "law_anti_telecom_fraud_2022_art018"],
  "gold_minimal_spans": ["law_anti_telecom_fraud_2022_art012", "law_anti_telecom_fraud_2022_art018"],
  "reference_answer": "《反电信网络诈骗法》在这里不能回答成抽象的“存在例外”。条文把物联网卡的常规管理、异常使用后的处置措施，以及反诈监测中可收集信息的用途边界写得很具体：电信业务经营者应先进行用户风险评估、实名登记并限定物联网卡功能和场景；发现异常使用时可以暂停服务、重新核验身份和使用场景；银行和支付机构在反诈监测中可以收集必要交易和设备信息，但不得挪作反电信网络诈骗以外用途。",
  "claims": [
    {
      "claim_text": "电信业务经营者销售物联网卡时，应建立用户风险评估制度；评估未通过的，不得销售，并应严格登记用户身份信息，限定物联网卡开通功能、使用场景和适用设备。",
      "claim_type": "general_rule",
      "gold_citations": ["law_anti_telecom_fraud_2022_art012"],
      "support_label": "supported",
      "requires_exception": true,
      "requires_multi_authority": false,
      "temporal_sensitive": false,
      "notes": "manual adjudication: baseline IoT card governance duty",
      "claim_id": "sample_0001_claim_1"
    },
    {
      "claim_text": "对存在异常使用情形的物联网卡，电信业务经营者应当采取暂停服务、重新核验身份和使用场景或者其他合同约定的处置措施。",
      "claim_type": "specific_exception",
      "gold_citations": ["law_anti_telecom_fraud_2022_art012"],
      "support_label": "supported",
      "requires_exception": false,
      "requires_multi_authority": false,
      "temporal_sensitive": false,
      "notes": "manual adjudication: event-triggered disposal measure",
      "claim_id": "sample_0001_claim_2"
    },
    {
      "claim_text": "银行业金融机构、非银行支付机构对异常账户和可疑交易进行监测时，可以收集必要的交易信息和设备位置信息，但上述信息未经客户授权，不得用于反电信网络诈骗以外的其他用途。",
      "claim_type": "general_rule_with_exception",
      "gold_citations": ["law_anti_telecom_fraud_2022_art018"],
      "support_label": "supported",
      "requires_exception": false,
      "requires_multi_authority": false,
      "temporal_sensitive": false,
      "notes": "manual adjudication: necessary collection with strict use limitation",
      "claim_id": "sample_0001_claim_3"
    }
  ],
  "answer_policy": {
    "allow_refusal": false,
    "must_mention_exception": true,
    "must_mention_temporal_validity": false
  },
  "split": "train"
}
```

对应分析记录：

| claim_id | 关注点 | 裁决解释 |
|---|---|---|
| `sample_0001_claim_1` | 是否是一般规则（销售前治理义务） | `supported`，由 `art012` 充分支持；该题要求必须提到例外边界（`requires_exception=true`） |
| `sample_0001_claim_2` | 是否是触发条件下的例外处置 | `supported`，同样由 `art012` 支持，类型为 `specific_exception` |
| `sample_0001_claim_3` | 是否同时表达“允许收集 + 禁止越用途” | `supported`，由 `art018` 支持，类型为 `general_rule_with_exception` |

## 标注与裁决文件

- `annotation/guidelines_v1.md`: 标注规范
- `annotation/schema_v1.json`: 标注 schema
- `annotation/claim_annotation_template.jsonl`: claim 模板
- `annotation/manual_adjudication_guide.md`: 人工裁决流程
- `annotation/manual_adjudication_queue.jsonl`: 待裁决队列
- `annotation/adjudication_log.jsonl`: 裁决日志
- `annotation/adjudication_summary.json`: 裁决统计摘要

## 发布状态

- 当前 benchmark 规模：`84/18/18`
- `benchmark_test` 中模板占位语句扫描：`0`
- 人工裁决队列：`0`
