# Annotation Guidelines v1

本文件定义 benchmark 的 claim 级标注规范、边界判断标准和人工裁决流程。

## 1. 目标与原则

标注目标不是“让答案看起来像法律回答”，而是构建可重复、可核验的 source-faithfulness 评测真值。

核心原则：

1. claim 必须是可独立判真的法律命题。
2. citation 必须达到“足以支持（sufficient）”，不是“看起来相关（relevant）”。
3. 例外、条件、程序、禁止应在需要时拆分，而不是混成一句套话。
4. 多法源题必须说明法源分工，不能只写“应综合判断”。

## 2. 标注单元

最小标注单元是单条 claim：

- `claim_text`
- `gold_citations`
- `support_label`
- `requires_exception`
- `requires_multi_authority`
- `temporal_sensitive`

每条 claim 都应满足：

- 单独可判断真假
- 单独可判断 citation sufficiency
- 不依赖其他 claim 才能成立

## 3. Claim 切分规则

### 3.1 应拆分的情形

以下内容应拆成多个 claim，而不是合并：

1. 一般规则与例外条款
2. 主体义务与禁止性边界
3. 触发条件与后续程序要求
4. 不同法源分别支持的结论片段

### 3.2 不合格 claim 形态

以下句式不能作为 gold claim：

- “该问题可由现行规范文本直接支持核心结论。”
- “完整回答应说明适用条件、主体范围或程序要求。”
- “如存在但书、例外或时效限制，答案应明确说明。”

这类句子属于标注提示语，不是法律命题。

## 4. Support Label 定义与边界

可用标签：

- `supported`
- `partially_supported`
- `unsupported`
- `conflicting`
- `insufficient_information`

### 4.1 `supported`

满足全部条件：

1. citation 直接对应 claim 关键法律要件
2. 无关键要件遗漏
3. 无超出条文文义的外推

### 4.2 `partially_supported`

至少有一部分被支持，但存在以下之一：

1. 覆盖了主结论但遗漏关键条件、限制或程序
2. citation 相关但不足以支持 claim 全部命题
3. 关键限定（主体/范围/时间）表达不完整

### 4.3 `unsupported`

claim 核心内容无法从 citation 推出。

### 4.4 `conflicting`

citation 与 claim 核心命题存在实质冲突。

### 4.5 `insufficient_information`

在给定法源范围与候选证据下，无法做出稳定判断；既不能确证支持，也不能确证冲突。

## 5. Citation Sufficiency 标准

### 5.1 必须同时满足

1. 命题关键术语与条文要件对应
2. 主体范围匹配
3. 适用场景匹配
4. 程序要求（如有）匹配
5. 时间或效力边界（如有）匹配

### 5.2 常见误判

1. “相关但不足”：条文提到了主题，但未覆盖 claim 的关键要件
2. “邻近误引”：引用了同一规范中相邻条文，但不是支持该 claim 的条文
3. “拼接过度”：把多个条文拼接成超出文义的综合结论

## 6. 例外与时效要求

当 `requires_exception=true` 时，答案必须显式覆盖：

1. 一般规则
2. 例外触发条件或但书
3. 不得绝对化的一般规则边界

当 `temporal_sensitive=true` 时，答案必须显式覆盖：

1. 时限
2. 生效/适用时间条件
3. 程序期限（如工作日要求）

## 7. 多法源题判断规则

当 `requires_multi_authority=true` 时，应满足：

1. 明确“法源 A 支持哪一部分 claim”
2. 明确“法源 B 支持哪一部分 claim”
3. 明确“单引 A 或单引 B 为什么不足”

不合格示例：

- “应综合两部规范判断。”（未分工）

## 8. 双标、复标与裁决流程

### 8.1 流程

1. 标注员 A 独立标注
2. 标注员 B 独立复标
3. 对分歧 claim 进入裁决
4. 记录到 `annotation/adjudication_log.jsonl`
5. 回写 benchmark 与 claim 模板

### 8.2 必须记录到裁决日志的情形

1. `supported` 与 `partially_supported` 边界分歧
2. citation 替换（错误映射、支持不足）
3. claim 拆分或合并
4. 多法源分工重写
5. 例外/时效遗漏修正

## 9. 文件同步要求

人工裁决后必须同步以下文件：

1. `data_processed/benchmark_train.jsonl`
2. `data_processed/benchmark_dev.jsonl`
3. `data_processed/benchmark_test.jsonl`
4. `annotation/claim_annotation_template.jsonl`
5. `annotation/adjudication_log.jsonl`

如果样本来自 queue，还需更新：

- `annotation/manual_adjudication_queue.jsonl`

## 10. 发布前 Gold 质检清单

每个待发布 split 至少完成：

1. 模板语句扫描为 0（草稿提示语、自动骨架语）
2. claim 逐条可判真
3. citation sufficiency 抽检通过
4. 例外题与多法源题抽检通过
5. 裁决日志覆盖多种分歧类型

建议将质检结果写入审计文件并随版本发布。
