# 贡献指南

本仓库不仅是代码仓库，也是一个 benchmark 数据仓库。因此，贡献质量不仅取决于脚本是否可运行，也取决于 citation 是否准确、gold 数据是否干净、人工裁决是否可追溯。

## 1. 适合贡献的内容

常见贡献类型包括：

- 修复解析、清洗或语料构建脚本
- 校正条文映射、article 对齐或 citation 选择
- 改进 benchmark 样本质量
- 增补或修订人工裁决记录
- 完善实验复现和评测文档

如果你的改动会影响 benchmark gold，请把它当作“数据治理改动”，而不是普通的文字润色。

## 2. 开始前建议先看

在修改 benchmark 或标注文件前，建议先阅读：

- [README.md](./README.md)
- [manual_revision_examples.md](./manual_revision_examples.md)
- [annotation/manual_adjudication_guide.md](./annotation/manual_adjudication_guide.md)
- [annotation/schema_v1.json](./annotation/schema_v1.json)
- [annotation/guidelines_v1.md](./annotation/guidelines_v1.md)

## 3. 人工判决工作流

自动扩展生成的样本可以作为草稿、候选标注单或训练前处理中间产物，但并不一定能直接作为最终评测 gold。凡是存在法律命题不具体、citation 不充分、法源分工不清、文本碎片污染等问题的样本，都需要人工判决。

### 3.1 什么时候必须人工判决

只要出现下列任一情况，都应进入人工判决流程：

1. 样本仍明显带有模板口吻，而不像真实法律答案
2. `claim_text` 过泛、带说明语气、无法独立判真
3. 一般规则和例外条款没有拆开
4. 多法源样本没有说明“哪部法支持哪部分结论”
5. 选中的 citation 只是“相关”，但还不够“足以支持”
6. 文本中混入 OCR 残留、页眉页脚、章节标题、断页碎片或错误条号
7. `support_label` 位于 `supported` 与 `partially_supported` 的争议边界

### 3.2 人工判决涉及的文件

人工判决工作包主要由以下文件组成：

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
```

### 3.3 各文件的作用

| 文件 | 作用 | 形式 |
| --- | --- | --- |
| `annotation/manual_adjudication_queue.jsonl` | 待人工处理样本队列 | JSONL，每行一个样本 |
| `annotation/adjudication_log.jsonl` | 分歧记录或重大裁决记录 | JSONL，每行一个 claim 级裁决 |
| `annotation/claim_annotation_template.jsonl` | claim 级同步模板 | JSONL，每行一个 claim |
| `data_processed/benchmark_*.jsonl` | 最终 benchmark 真正生效的正式文件 | JSONL，每行一个完整样本 |

## 4. 人工判决后必须回写什么

如果你人工判决了一个样本，不能只修改 queue 或 log，而必须同步回写到正式数据：

1. 在对应的 `data_processed/benchmark_*.jsonl` 中重写样本
2. 将对应 claim 同步到 `annotation/claim_annotation_template.jsonl`
3. 如果存在分歧或重大调整，向 `annotation/adjudication_log.jsonl` 追加记录
4. 如果样本原本来自 `annotation/manual_adjudication_queue.jsonl`，处理完成后应移除或标记为已解决

不要让 benchmark、template、log 三者脱节。

## 5. 待裁决队列的建议格式

推荐的 `manual_adjudication_queue.jsonl` 行格式如下：

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

常用的 `review_flags` 可以包括：

- `generic_exception_requires_manual_review`
- `generic_multi_authority_requires_manual_review`
- `citation_sufficiency_requires_manual_review`
- `ocr_fragment_requires_manual_review`
- `support_label_boundary_requires_manual_review`

## 6. 裁决日志的建议格式

推荐的 `adjudication_log.jsonl` 行格式如下：

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

以下情况建议写入裁决日志：

- 两位标注者对同一 claim 判断不同
- citation 被替换，因为原 citation 是错误的或支持不足
- 一个 claim 被拆分、合并或改写为新的法律命题
- 样本实质上改变了题型理解，例如从泛泛的例外题改成具体条件题

## 7. Gold 样本通过前检查清单

在认为一个样本已经完成前，请确认以下事项全部成立：

1. `reference_answer` 像真实法律回答，而不是标注说明
2. 每个 `claim_text` 都是具体法律命题
3. 每个 claim 都能独立核验
4. `gold_citations` 对该 claim 是“足以支持”，而非仅仅“相关”
5. 例外、条件、禁止和程序义务在需要时已经拆开
6. 多法源样本已经明确各法源分工
7. 不再残留 OCR 噪声、章节标题、页码或断句碎片

## 8. 提交时的边界控制

请尽量不要把 benchmark 治理改动和无关实验文件混在一起提交。

如果本次提交的重点是 benchmark / adjudication，建议只包含：

- 实际被改动的 benchmark 文件
- 已同步的 annotation 文件
- 为这些改动服务的说明文档

尽量不要顺手混入：

- 临时 mock 输出
- 本地评测缓存或 scratch 文件
- 尚未整理好的脚本实验

## 9. 推荐的提交信息风格

可以参考以下写法：

- `Refine benchmark gold for multi-authority samples`
- `Fix citation mapping for PIPL procedural questions`
- `Add adjudication guide and README-ready revision examples`
