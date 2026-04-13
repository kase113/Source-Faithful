一、项目目标

构建一个 中文官方法规场景 下的 legal RAG benchmark，用于评测：

引用是否真实存在
引用是否相关
引用是否足以支持答案中的法律主张
是否存在规范误适用
是否遗漏关键例外
是否存在检索错配

数据范围：你们前面定下的 30 个法源文本。
任务单位：问题 -> 检索 -> 回答 -> claim-level citation support

二、可直接执行的数据采集清单
2.1 采集总原则

只采：

官方公开来源
现行有效文本
能保留原始链接和抓取时间
能定位到“条/款/项”的文本

每一部法源都必须保存：

原始网页链接
原始 HTML 或下载文件
抓取时间
标准化文本
条款切分结果
2.2 数据目录结构

建议直接建这个目录：

project_root/
  data_raw/
    flk/
      html/
      pdf/
      doc/
      metadata_raw.jsonl
    moj/
      html/
      pdf/
      doc/
      metadata_raw.jsonl
    cac/
      html/
      pdf/
      doc/
      metadata_raw.jsonl

  data_processed/
    authority_docs.jsonl
    authority_articles.jsonl
    retrieval_chunks.jsonl
    question_pool.jsonl
    benchmark_train.jsonl
    benchmark_dev.jsonl
    benchmark_test.jsonl

  annotation/
    guidelines_v1.md
    schema_v1.json
    adjudication_log.jsonl

  scripts/
    crawl/
    parse/
    build_dataset/
    eval/
2.3 法源清单台账

先做一个总表，建议文件名：

authority_master_sheet.csv

字段如下：

字段名	含义
authority_id	唯一 ID
title	法源标题
short_name	简称
level	法律 / 行政法规 / 部门规章 / 司法解释
domain	数据合规 / 网络安全 / 平台治理 / AI治理
issuing_body	发布机关
issue_date	公布日期
effective_date	生效日期
current_status	现行有效/修订中等
source_site	flk / moj / cac / gov
source_url	原始链接
file_url	pdf/doc 下载链接
crawl_status	未抓取/已抓取/失败
parse_status	未解析/已解析/需人工修复
notes	备注
2.4 30 个法源的采集优先级
一级核心 12 个

先采这 12 个，做 pilot。

网络安全法
数据安全法
个人信息保护法
网络数据安全管理条例
关键信息基础设施安全保护条例
网络安全审查办法
数据出境安全评估办法
个人信息出境标准合同办法
促进和规范数据跨境流动规定
互联网信息服务算法推荐管理规定
互联网信息服务深度合成管理规定
生成式人工智能服务管理暂行办法
二级扩展 18 个

后续扩展到 30。

密码法
电子签名法
民法典中隐私权和个人信息保护相关条款
反电信网络诈骗法
未成年人保护法
商用密码管理条例
未成年人网络保护条例
保守国家秘密法实施条例
国务院关于在线政务服务的若干规定
汽车数据安全管理若干规定（试行）
互联网用户账号信息管理规定
网络信息内容生态治理规定
儿童个人信息网络保护规定
区块链信息服务管理规定
电信和互联网用户个人信息保护规定
互联网新闻信息服务管理规定
网络暴力信息治理规定
网信部门行政执法程序规定
2.5 每个法源的采集任务卡

你们可以给每个法源做一张任务卡：

法源任务卡模板
authority_id：
title：
source_site：
source_url：
download_url_pdf：
download_url_doc：
assigned_to：
crawl_date：
html_saved：Y/N
file_saved：Y/N
metadata_checked：Y/N
article_split_checked：Y/N
final_status：done / fix / pending
2.6 抓取流程
Step 1：建立白名单

不要先写全站爬虫。
先把这 30 个法源的链接手工确认到 authority_master_sheet.csv。

Step 2：抓取原始页

每个法源保存：

原始 HTML
下载文件 PDF/Word
页面截图或快照可选
Step 3：抽取元数据

抽以下字段：

标题
发布机关
法源层级
公布日期
生效日期
效力状态
历史沿革
正文全文
Step 4：切分正文

切成：

article_no
paragraph_no
item_no
text
Step 5：人工抽查

每个法源至少检查：

标题是否正确
条号是否完整
正文是否缺字
例外条款是否被切坏
三、处理后数据的 3 层结构

你们处理完后，应该有 3 份核心文件。

3.1 authority_docs.jsonl

文档级。

{
  "authority_id": "law_pipl_2021",
  "title": "中华人民共和国个人信息保护法",
  "short_name": "个人信息保护法",
  "level": "法律",
  "issuing_body": "全国人民代表大会常务委员会",
  "issue_date": "2021-08-20",
  "effective_date": "2021-11-01",
  "status": "现行有效",
  "source_site": "flk",
  "source_url": "https://...",
  "full_text": "...",
  "domain_tags": ["个人信息", "数据合规"]
}
3.2 authority_articles.jsonl

条款级。

{
  "article_id": "law_pipl_2021_art013",
  "authority_id": "law_pipl_2021",
  "article_no": "第十三条",
  "paragraph_no": null,
  "item_no": null,
  "text": "符合下列情形之一的，个人信息处理者方可处理个人信息：...",
  "char_start": 10234,
  "char_end": 10482,
  "topic_tags": ["处理依据", "同意例外"]
}
3.3 retrieval_chunks.jsonl

检索单元级。

{
  "chunk_id": "chunk_pipl_art013_p1",
  "authority_id": "law_pipl_2021",
  "article_id": "law_pipl_2021_art013",
  "chunk_type": "article",
  "text": "符合下列情形之一的，个人信息处理者方可处理个人信息：...",
  "citation_label": "《个人信息保护法》第十三条",
  "level": "法律",
  "effective_date": "2021-11-01",
  "domain_tags": ["个人信息", "同意例外"]
}
四、数据构造清单

这是第二阶段。
是的，一定是在法源采集完成之后再做。

4.1 benchmark 样本构造目标

每条 benchmark 样本包含：

一个法律问题
一个参考答案
2 到 4 个 claim
每个 claim 的 gold citation
最小支持片段
错误类型标签空间
4.2 问题来源

建议三路并行。

路线 A：法条逆向写题

最稳。

示例：

条文：第十三条 同意例外
问题：在哪些情形下可以不经个人同意处理个人信息？
路线 B：例外条款优先写题

最有研究味。

示例：

问题：处理个人信息是否一律需要取得同意？
gold：需要引用一般规则 + 例外条款
路线 C：LLM 生成草案，人工筛选

最高效。

流程：

输入法条
让 LLM 生成 3 个问题、1 个参考答案
人工保留最自然、最可核验的一条
4.3 问题类型配比

建议在 question_pool 里控制比例：

类型	占比
直接法条问答	25%
条件/要件问答	20%
例外/但书问答	25%
程序义务问答	15%
多法源联合问答	15%

这会让 benchmark 不至于过于简单。

五、标注 schema

下面这部分最关键。

5.1 标注对象层级

你们要标 4 层：

层 1：问题级

问题整体对应哪些法源。

层 2：答案级

参考答案是否完整、是否需要拒答。

层 3：claim 级

答案中的每个关键主张。

层 4：citation 级

每个 claim 对应的法源支持关系。

5.2 benchmark 样本 schema

建议主文件 benchmark_*.jsonl 用这个结构：

{
  "sample_id": "sample_0001",
  "domain": "数据合规",
  "question": "在哪些情形下可以不经个人同意处理个人信息？",
  "question_type": "例外条款问答",
  "authority_scope": [
    "law_pipl_2021"
  ],
  "gold_authorities": [
    "law_pipl_2021_art013"
  ],
  "gold_minimal_spans": [
    "law_pipl_2021_art013"
  ],
  "reference_answer": "在符合法定情形时，个人信息处理者可以不经个人同意处理个人信息，例如为订立、履行合同所必需，或者为履行法定职责义务所必需等。",
  "claims": [
    {
      "claim_id": "sample_0001_claim_1",
      "claim_text": "并非所有个人信息处理都必须取得个人同意。",
      "claim_type": "general_rule_with_exception",
      "gold_citations": [
        "law_pipl_2021_art013"
      ],
      "support_label": "supported",
      "requires_exception": true,
      "notes": ""
    },
    {
      "claim_id": "sample_0001_claim_2",
      "claim_text": "在为订立、履行合同所必需等法定情形下，可以不经同意处理个人信息。",
      "claim_type": "specific_exception",
      "gold_citations": [
        "law_pipl_2021_art013"
      ],
      "support_label": "supported",
      "requires_exception": false,
      "notes": ""
    }
  ],
  "answer_policy": {
    "allow_refusal": false,
    "must_mention_exception": true,
    "must_mention_temporal_validity": false
  },
  "split": "train"
}
5.3 claim 标注字段定义

每个 claim 至少标这些：

字段	含义
claim_id	主张 ID
claim_text	主张文本
claim_type	主张类型
gold_citations	正确引用
support_label	支持关系
requires_exception	是否必须提到例外
requires_multi_authority	是否必须引用多个法源
temporal_sensitive	是否涉及时效/版本
notes	备注
5.4 claim_type 枚举

建议固定成以下枚举：

definition
general_rule
specific_obligation
specific_prohibition
procedural_requirement
exception
scope_of_application
cross_border_requirement
enforcement_consequence
general_rule_with_exception
5.5 support_label 枚举

这是你们论文最重要的标注标签。

建议标签
supported
partially_supported
unsupported
conflicting
insufficient_information
定义

supported
引用的法源真实、相关，且足以支持该 claim。

partially_supported
引用相关，但支持不完整；可能漏条件、漏限定、漏程序。

unsupported
引用存在，但不支持该 claim。

conflicting
存在相反或限制性法源，被当前 claim 忽略。

insufficient_information
单靠给定法源无法得出该结论，应拒答或补充条件。

六、模型输出评测 schema

为了后续自动评测，你们还需要一个模型输出格式。

6.1 统一输出格式

让模型按 JSON 输出：

{
  "final_answer": "……",
  "claims": [
    {
      "claim_text": "……",
      "citations": ["《个人信息保护法》第十三条"],
      "confidence": 0.82
    }
  ],
  "refusal": false,
  "refusal_reason": ""
}

这样你们后面可以自动抽 citation 和 claim。

6.2 模型输出误差标签

人工评估模型输出时，给每个 claim 标这些错误标签：

fabricated_citation
citation_not_found_in_corpus
irrelevant_citation
insufficient_citation
norm_misapplication
exception_omitted
temporal_mismatch
retrieval_mismatch
should_have_refused
七、标注流程
7.1 角色分工
标注员 A

主标。

标注员 B

复标 20% 到 30%。

裁决员

处理分歧，建议由法律背景更强的人担任。

7.2 标注步骤
Step 1

读取问题和候选 gold 法条。

Step 2

写 reference answer。

Step 3

把 answer 切成 2 到 4 个 claim。

Step 4

为每个 claim 指定 gold citation。

Step 5

判断是否必须提及例外、时间、限定条件。

Step 6

另一位标注员抽样复核。

Step 7

记录分歧到 adjudication_log.jsonl。

7.3 分歧记录 schema
{
  "sample_id": "sample_0001",
  "claim_id": "sample_0001_claim_2",
  "annotator_a": "supported",
  "annotator_b": "partially_supported",
  "final_label": "partially_supported",
  "reason": "条文支持基本结论，但需要补充法定范围限定。"
}